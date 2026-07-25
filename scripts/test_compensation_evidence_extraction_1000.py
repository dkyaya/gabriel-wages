#!/usr/bin/env python3
"""Offline tests for cumulative provisional 1,000-document extraction."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_compensation_evidence_extraction.py"
spec = importlib.util.spec_from_file_location("compensation_extraction_1000", RUNNER)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load compensation extraction runner")
extract = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = extract
spec.loader.exec_module(extract)


def packet(page: int = 2) -> extract.PagePacket:
    return extract.PagePacket(
        page=page,
        role="candidate",
        text="Base salary schedule effective July 1 with rank and step columns.",
        image="",
        wage=2,
        numeric=1,
        table=3,
        qual=1,
        nonbase=0,
        reference=False,
    )


def selection(case_id: str, lane: str) -> dict[str, str]:
    row = {field: "" for field in extract.SELECTION_1000_FIELDS}
    row.update(
        {
            "selection_rank": "501",
            "extraction_case_id": case_id,
            "document_identity_id": f"doc_{case_id}",
            "text_table_detection_id": f"ttd_{case_id}",
            "source_review_id": f"sr_{case_id}",
            "candidate_queue_row_id": f"cq_{case_id}",
            "state": "ZZ",
            "municipality": "Testville",
            "government_name": "City of Testville",
            "unit_type": "police",
            "candidate_source_type": "cba",
            "content_artifact_path": "bounded.pdf",
            "content_hash": case_id,
            "pdf_page_count": "3",
            "candidate_wage_pages": "2",
            "planned_lane": lane,
            "cumulative_cohort": "new_500_scale",
            "requires_gabriel": "yes",
        }
    )
    return row


def response() -> dict[str, object]:
    return {
        "case_disposition": "quantitative_ready",
        "page_relationship": "exact_evidence_page",
        "quantitative_observations": [
            {
                "page_number": 2,
                "compensation_type": "annual_salary",
                "occupation_unit_classification_rank": "Officer step 1",
                "rate_value": "",
                "salary_value": "50000",
                "hourly_rate": "",
                "annual_salary": "50000",
                "pay_band": "",
                "step": "1",
                "grade": "",
                "percentage_increase": "",
                "effective_date": "2026-07-01",
                "currency_or_unit": "USD annual",
                "confidence": "high",
                "reason_code": "BASE_SALARY_SCHEDULE",
            }
        ],
        "qualitative_observations": [],
        "non_base_wage_observations": [],
        "confidence": "high",
        "reason_codes": ["BASE_SALARY_SCHEDULE"],
        "short_rationale": "The bounded page shows base salary by rank and step.",
    }


class CompensationExtraction1000Tests(unittest.TestCase):
    def test_modes_are_backward_compatible(self) -> None:
        choices = extract.parse_args(
            ["--mode", "freeze_500_selection", "--output-dir", "/tmp/x"]
        )
        self.assertEqual(choices.mode, "freeze_500_selection")
        for mode in ("freeze_1000_selection", "preflight_1000", "live_lanes_1000"):
            parsed = extract.parse_args(
                ["--mode", mode, "--output-dir", "/tmp/x", "--case-limit", "1000"]
            )
            self.assertEqual(parsed.mode, mode)

    def test_real_cumulative_selection_is_exact_and_preserves_seed(self) -> None:
        protected = [
            extract.EXTRACTION_500_DIR / "compensation_extraction_500_selection_manifest.csv",
            extract.TARGETED_QA_500_DIR / "compensation_extraction_500_recomputed_decision.json",
            extract.GATE3,
            extract.DETECTION,
            extract.READINESS,
            extract.SOURCE_REVIEW,
        ]
        before = {path: extract.sha_file(path) for path in protected}
        with tempfile.TemporaryDirectory() as temp:
            rows = extract.freeze_selection_1000(
                extract.GATE3, extract.TARGETED_QA_500_DIR, Path(temp), 1000
            )
        seed = extract.read_csv(
            extract.EXTRACTION_500_DIR / "compensation_extraction_500_selection_manifest.csv"
        )
        self.assertEqual(len(rows), 1000)
        self.assertEqual(len({row["document_identity_id"] for row in rows}), 1000)
        self.assertEqual(len({row["content_hash"] for row in rows}), 1000)
        self.assertEqual(sum(row["requires_gabriel"] == "no" for row in rows), 500)
        self.assertEqual(sum(row["requires_gabriel"] == "yes" for row in rows), 500)
        self.assertEqual(
            [row["document_identity_id"] for row in rows[:500]],
            [row["document_identity_id"] for row in seed],
        )
        self.assertEqual(
            {
                unit: sum(row["unit_type"] == unit for row in rows)
                for unit in ("police", "fire", "non_safety")
            },
            {"police": 363, "fire": 237, "non_safety": 400},
        )
        self.assertTrue(all(row["matched_non_safety_case_id"] for row in rows))
        self.assertEqual(before, {path: extract.sha_file(path) for path in protected})

    def test_quantitative_schema_routes_nonbase_and_rejects_other_dump(self) -> None:
        valid = response()
        self.assertEqual(
            extract.validate_response(json.dumps(valid), {2})["case_disposition"],
            "quantitative_ready",
        )
        overtime = response()
        overtime["quantitative_observations"][0].update(
            {
                "compensation_type": "other",
                "occupation_unit_classification_rank": "",
                "salary_value": "",
                "annual_salary": "",
                "rate_value": "1.5 times regular rate overtime premium",
                "reason_code": "OVERTIME_PREMIUM",
            }
        )
        with self.assertRaises(ValueError):
            extract.validate_response(json.dumps(overtime), {2})
        vague_other = response()
        vague_other["quantitative_observations"][0].update(
            {
                "compensation_type": "other",
                "salary_value": "",
                "annual_salary": "",
                "rate_value": "$500",
                "reason_code": "OTHER_COMP",
            }
        )
        with self.assertRaises(ValueError):
            extract.validate_response(json.dumps(vague_other), {2})

    def test_prompt_is_bounded_and_excludes_prior_labels(self) -> None:
        text = extract.prompt(selection("new_case", "quantitative"), [packet()])
        self.assertLess(len(text), 10000)
        lowered = text.lower()
        for forbidden in ("review1", "review2", "gate 1 label", "gate 2 label", "gate 3 label"):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("base wage", lowered)
        self.assertIn("non-base", lowered)

    def test_six_path_preflight_calls_only_new_cases_and_saves_no_raw(self) -> None:
        lanes = [
            "quantitative",
            "qualitative",
            "mixed",
            "non_base_wage",
            "reference_and_exclusion",
            "quantitative",
        ]
        rows = [selection(f"case_{index}", lane) for index, lane in enumerate(lanes)]
        seed = selection("seed_case", "mixed")
        seed.update(
            {
                "cumulative_cohort": "corrected_500_seed",
                "requires_gabriel": "no",
            }
        )
        packet_map = {row["extraction_case_id"]: [packet()] for row in rows}

        def fake_call(requests, key, parallel):
            self.assertEqual(key, "redacted-test-key")
            self.assertEqual(parallel, 1)
            self.assertNotIn("seed_case", {request.row["extraction_case_id"] for request in requests})
            return [
                extract.Result(
                    case_id=request.row["extraction_case_id"],
                    status="success",
                    request_id=f"req_{index}",
                    raw=json.dumps(response()),
                    parsed=response(),
                    elapsed=0.01,
                    input_tokens=10,
                    output_tokens=10,
                    total_tokens=20,
                    error_type="",
                    error_message="",
                    prompt_hash="abc",
                    prompt_chars=100,
                    image_count=0,
                    image_bytes=0,
                )
                for index, request in enumerate(requests)
            ]

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            with mock.patch.object(extract, "call_gabriel", side_effect=fake_call):
                self.assertEqual(
                    extract.preflight_1000(output, [seed, *rows], packet_map, "redacted-test-key"),
                    0,
                )
            marker = json.loads((output / ".preflight_1000_passed.json").read_text())
            self.assertEqual(marker["schema_valid_count"], 6)
            self.assertEqual(marker["seed_case_calls"], 0)
            names = {path.name for path in output.iterdir()}
            self.assertFalse(any("prompt" in name or "response" in name for name in names))

    def test_bounded_packet_limits_are_unchanged(self) -> None:
        pages = [packet(page) for page in range(1, 7)]
        self.assertLessEqual(len(pages), 6)
        self.assertTrue(all(len(page.text) <= 1500 for page in pages))
        self.assertLessEqual(sum(len(page.text) for page in pages), 6000)
        source = RUNNER.read_text(encoding="utf-8")
        for forbidden_write in ("raw_prompt.json", "raw_response.json", "full_page_text"):
            self.assertNotIn(forbidden_write, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
