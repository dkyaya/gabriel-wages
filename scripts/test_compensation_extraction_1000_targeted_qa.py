#!/usr/bin/env python3
"""Offline regression tests for cumulative 1,000-document targeted QA."""

from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_compensation_extraction_1000_targeted_qa.py"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("targeted_qa_1000", RUNNER)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load cumulative targeted-QA runner")
qa = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = qa
spec.loader.exec_module(qa)


def sample_quant(**updates: str) -> dict[str, str]:
    row = {
        "quantitative_observation_id": "qobs_sample",
        "extraction_case_id": "case_sample",
        "mixed_join_key": "mix_sample",
        "document_identity_id": "doc_sample",
        "text_table_detection_id": "ttd_sample",
        "source_review_id": "sr_sample",
        "candidate_queue_row_id": "cq_sample",
        "state": "ZZ",
        "municipality": "Testville",
        "government_name": "City of Testville",
        "unit_type": "police",
        "candidate_source_type": "cba",
        "contract_period_start": "2025",
        "contract_period_end": "2027",
        "page_number": "2",
        "compensation_type": "percentage_increase",
        "occupation_unit_classification_rank": "Officer",
        "rate_value": "",
        "salary_value": "",
        "hourly_rate": "",
        "annual_salary": "",
        "pay_band": "",
        "step": "",
        "grade": "",
        "percentage_increase": "5%",
        "effective_date": "2026-01-01",
        "currency_or_unit": "percent of base wage",
        "bounded_evidence_pointer": "local.pdf#page=2",
        "confidence": "high",
        "reason_code": "CERTIFICATION_PAY",
        "qa_status": "needs_review",
        "cumulative_cohort": "new_500_live",
        "source_seed_observation_id": "",
        "qa_original_status": "needs_review",
        "qa_resolution_classification": "insufficient_evidence_needs_review",
        "qa_resolution_status": "unresolved",
        "canonical_observation_id": "qobs_sample",
        "duplicate_of": "",
        "active_in_provisional_lane": "true",
    }
    row.update(updates)
    return row


class CumulativeTargetedQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name) / "qa_output"
        cls.before = {
            name: qa.qa500.sha_file(qa.SOURCE_DIR / name)
            for name in (
                qa.REVIEW,
                qa.DECISION,
                qa.PACKET,
                qa.SELECTION,
                qa.QUANT,
                qa.QUAL,
                qa.MIXED,
                qa.NONBASE,
                qa.REFERENCE,
            )
        }
        cls.result = qa.resolve(qa.SOURCE_DIR, cls.output, write=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def test_exact_151_scope_and_126_routing_rows(self) -> None:
        resolutions = self.result["resolutions"]
        self.assertEqual(len(resolutions), 151)
        routing = [
            row
            for row in resolutions
            if row["review_type"] == "possible_non_base_wage_quantitative"
        ]
        self.assertEqual(len(routing), 126)
        self.assertTrue(all(row["resolution_status"] == "resolved" for row in routing))
        self.assertTrue(all(row["reason_codes"] for row in routing))
        self.assertNotIn(
            "insufficient_evidence_needs_review",
            {row["resolution_classification"] for row in routing},
        )

    def test_reroutes_preserve_source_ids_and_join_keys(self) -> None:
        rows = self.result["rows"]["nonbase"]
        created = [row for row in rows if row.get("source_quantitative_observation_id")]
        self.assertEqual(
            len(created),
            self.result["summary"]["new_non_base_wage_records_created"],
        )
        self.assertTrue(all(row["source_quantitative_observation_id"] for row in created))
        source = {
            row["quantitative_observation_id"]: row
            for row in self.result["rows"]["quant"]
        }
        for row in created:
            original = source[row["source_quantitative_observation_id"]]
            self.assertEqual(row["bounded_evidence_pointer"], original["bounded_evidence_pointer"])
            self.assertEqual(row["source_mixed_join_key"], original["mixed_join_key"])

    def test_split_helper_preserves_shared_join_key(self) -> None:
        original = sample_quant()
        retained, nonbase = qa.split_quant_and_nonbase(
            qa.targeted_defaults(original, original["quantitative_observation_id"]),
            "education_or_certification",
            "qares_test",
        )
        self.assertEqual(retained["mixed_join_key"], "mix_sample")
        self.assertEqual(nonbase["source_mixed_join_key"], "mix_sample")
        self.assertEqual(
            nonbase["source_quantitative_observation_id"],
            original["quantitative_observation_id"],
        )

    def test_conflict_rate_and_gate_recompute(self) -> None:
        summary = self.result["summary"]
        decision = self.result["decision"]
        self.assertEqual(summary["conflict_group_count"], 25)
        self.assertEqual(summary["unresolved_conflict_group_count"], 2)
        self.assertLessEqual(summary["unresolved_quantitative_conflict_rate"], 0.02)
        self.assertEqual(summary["unresolved_base_non_base_contamination_count"], 0)
        self.assertTrue(decision["qa_pass"])
        self.assertTrue(decision["remaining_readable_parse_text_extraction_allowed"])

    def test_duplicate_ids_and_page_pointers_remain_zero(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["duplicate_observation_id_count"], 0)
        self.assertEqual(summary["invalid_observation_page_count"], 0)
        self.assertEqual(summary["existing_duplicate_observations_preserved"], 9)

    def test_shadow_outputs_do_not_overwrite_inputs(self) -> None:
        after = {name: qa.qa500.sha_file(qa.SOURCE_DIR / name) for name in self.before}
        self.assertEqual(self.before, after)
        for output_name in qa.OUTPUT_NAMES.values():
            self.assertNotEqual((self.output / output_name).resolve(), (qa.SOURCE_DIR / output_name).resolve())

    def test_corrected_mixed_rows_preserve_original_membership(self) -> None:
        changed = [
            row
            for row in self.result["rows"]["mixed"]
            if row["targeted_qa_resolution_classification"] == "mixed_membership_corrected"
        ]
        self.assertTrue(changed)
        self.assertTrue(
            all(row["targeted_qa_original_quantitative_observation_ids"] for row in changed)
        )

    def test_no_network_model_or_extraction_code_path(self) -> None:
        source = RUNNER.read_text(encoding="utf-8").lower()
        for forbidden in (
            "requests.",
            "httpx.",
            "urllib.request",
            "openai",
            "gabriel.call",
            "run_live_extraction",
        ):
            self.assertNotIn(forbidden, source)

    def test_resolution_ledger_matches_written_csv(self) -> None:
        with (self.output / qa.OUTPUT_NAMES["resolutions"]).open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 151)
        self.assertEqual(
            sum(row["review_type"] == "possible_non_base_wage_quantitative" for row in rows),
            126,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
