#!/usr/bin/env python3
"""Offline tests for cumulative provisional 1,000-document extraction."""

from __future__ import annotations

import importlib.util
import json
import shutil
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


def qualitative_observation() -> dict[str, object]:
    return {
        "page_number": 2,
        "mechanism_type": "implementation_or_effective_date_logic",
        "bargaining_logic": "",
        "indexing_formula": "",
        "comparability_basis": "",
        "parity_logic": "",
        "step_progression_rule": "",
        "eligibility_rule": "",
        "implementation_rule": "The base schedule takes effect on the listed date.",
        "fiscal_constraint": "",
        "reopener_clause": "",
        "differentiation_logic": "Base salary varies by rank and step.",
        "confidence": "high",
        "reason_code": "BASE_EFFECTIVE_DATE_RULE",
    }


def nonbase_observation() -> dict[str, object]:
    return {
        "page_number": 2,
        "non_base_wage_type": "stipend",
        "value_text": "$500",
        "effective_date": "",
        "eligibility_or_implementation_rule": "Eligible certified employees.",
        "confidence": "medium",
        "reason_code": "CERTIFICATION_STIPEND",
    }


def longevity_response() -> dict[str, object]:
    value = response()
    value.update(
        {
            "case_disposition": "non_base_wage",
            "quantitative_observations": [],
            "qualitative_observations": [],
            "non_base_wage_observations": [
                {
                    "page_number": 2,
                    "non_base_wage_type": "longevity",
                    "value_text": "$500",
                    "effective_date": "",
                    "eligibility_or_implementation_rule": (
                        "Employees qualify after the stated service period."
                    ),
                    "confidence": "high",
                    "reason_code": "LONGEVITY_NON_BASE",
                }
            ],
            "reason_codes": ["LONGEVITY_NON_BASE"],
            "short_rationale": "The bounded evidence is longevity pay only.",
        }
    )
    return value


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
        frozen_selection = (
            ROOT
            / "docs/analysis/compensation_extraction"
            / "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25"
            / "compensation_extraction_1000_selection_manifest.csv"
        )
        expected_hash = (
            "147e311e7a6d6c3aeb98c52357f6d46e"
            "a8ee52798be45493bf0a1c138a3b9f15"
        )
        self.assertEqual(extract.sha_file(frozen_selection), expected_hash)
        protected = [
            frozen_selection,
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

    def test_mixed_ready_missing_quantitative_subrecords_fails_closed(self) -> None:
        value = response()
        value["case_disposition"] = "mixed_ready"
        value["quantitative_observations"] = []
        value["qualitative_observations"] = [qualitative_observation()]
        with self.assertRaisesRegex(ValueError, "mixed_ready requires"):
            extract.validate_response(json.dumps(value), {2})

    def test_mixed_ready_missing_qualitative_subrecords_fails_closed(self) -> None:
        value = response()
        value["case_disposition"] = "mixed_ready"
        value["qualitative_observations"] = []
        with self.assertRaisesRegex(ValueError, "mixed_ready requires"):
            extract.validate_response(json.dumps(value), {2})

    def test_disposition_matrix_accepts_only_supported_evidence_family(self) -> None:
        quantitative = response()
        self.assertEqual(
            extract.validate_response(json.dumps(quantitative), {2})[
                "case_disposition"
            ],
            "quantitative_ready",
        )

        qualitative = response()
        qualitative["case_disposition"] = "qualitative_ready"
        qualitative["quantitative_observations"] = []
        qualitative["qualitative_observations"] = [qualitative_observation()]
        self.assertEqual(
            extract.validate_response(json.dumps(qualitative), {2})[
                "case_disposition"
            ],
            "qualitative_ready",
        )

        mixed = response()
        mixed["case_disposition"] = "mixed_ready"
        mixed["qualitative_observations"] = [qualitative_observation()]
        self.assertEqual(
            extract.validate_response(json.dumps(mixed), {2})[
                "case_disposition"
            ],
            "mixed_ready",
        )

        nonbase = response()
        nonbase["case_disposition"] = "non_base_wage"
        nonbase["quantitative_observations"] = []
        nonbase["non_base_wage_observations"] = [nonbase_observation()]
        self.assertEqual(
            extract.validate_response(json.dumps(nonbase), {2})[
                "case_disposition"
            ],
            "non_base_wage",
        )

        invalid_quant = response()
        invalid_quant["qualitative_observations"] = [qualitative_observation()]
        with self.assertRaisesRegex(ValueError, "quantitative_ready requires"):
            extract.validate_response(json.dumps(invalid_quant), {2})

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

    def test_longevity_onecase_contract_rejects_base_and_accepts_nonbase(self) -> None:
        invalid = response()
        invalid["quantitative_observations"][0].update(
            {
                "compensation_type": "other",
                "occupation_unit_classification_rank": "longevity schedule",
                "rate_value": "$500 longevity payment",
                "salary_value": "",
                "annual_salary": "",
                "reason_code": "LONGEVITY_PAY",
            }
        )
        with self.assertRaisesRegex(ValueError, "non-base compensation"):
            extract.validate_longevity_onecase_response(
                json.dumps(invalid), {2}
            )
        valid = longevity_response()
        parsed = extract.validate_longevity_onecase_response(
            json.dumps(valid), {2}
        )
        self.assertEqual(parsed["case_disposition"], "non_base_wage")
        self.assertEqual(parsed["quantitative_observations"], [])
        self.assertEqual(parsed["qualitative_observations"], [])
        self.assertEqual(
            parsed["non_base_wage_observations"][0]["non_base_wage_type"],
            "longevity",
        )

    def test_prompt_is_bounded_and_excludes_prior_labels(self) -> None:
        row = selection("new_case", "quantitative")
        text = extract.prompt(row, [packet()])
        self.assertLess(len(text), 10000)
        lowered = text.lower()
        for forbidden in ("review1", "review2", "gate 1 label", "gate 2 label", "gate 3 label"):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("base wage", lowered)
        self.assertIn("non-base", lowered)
        row["_nonbase_retry_hint"] = "longevity"
        retry_text = extract.prompt(row, [packet()])
        self.assertIn("prior strict-validation attempt", retry_text)
        self.assertIn("'longevity'", retry_text)
        self.assertIn("hard exclusion from the quantitative array", retry_text)
        self.assertIn("completely independent of that non-base family", retry_text)
        self.assertIn("never fabricate a base item", retry_text)

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
            prior_metadata = {field: "" for field in extract.METADATA_FIELDS}
            prior_metadata.update(
                {
                    "request_phase": "live_1000",
                    "extraction_case_id": "previous_live_case",
                    "request_status": "success",
                    "schema_valid": "true",
                }
            )
            prior_timing = {field: "" for field in extract.TIMING_FIELDS}
            prior_timing.update(
                {
                    "request_phase": "live_1000",
                    "extraction_case_id": "previous_live_case",
                    "request_status": "success",
                }
            )
            extract.write_csv(
                output / "compensation_extraction_1000_request_metadata.csv",
                extract.METADATA_FIELDS,
                [prior_metadata],
            )
            extract.write_csv(
                output / "compensation_extraction_1000_timing.csv",
                extract.TIMING_FIELDS,
                [prior_timing],
            )
            with mock.patch.object(extract, "call_gabriel", side_effect=fake_call):
                self.assertEqual(
                    extract.preflight_1000(output, [seed, *rows], packet_map, "redacted-test-key"),
                    0,
                )
            marker = json.loads((output / ".preflight_1000_passed.json").read_text())
            self.assertEqual(marker["schema_valid_count"], 6)
            self.assertEqual(marker["seed_case_calls"], 0)
            metadata = extract.read_csv(
                output / "compensation_extraction_1000_request_metadata.csv"
            )
            self.assertEqual(len(metadata), 7)
            self.assertEqual(metadata[-1]["extraction_case_id"], "previous_live_case")
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

    def test_onecase_modes_send_only_unresolved_case_and_complete_checkpoint(self) -> None:
        real_output = (
            ROOT
            / "docs/analysis/compensation_extraction"
            / "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25"
        )
        copied = (
            "compensation_extraction_1000_selection_manifest.csv",
            "compensation_extraction_1000_new_case_results.jsonl",
            "compensation_extraction_1000_request_metadata.csv",
            "compensation_extraction_1000_timing.csv",
        )
        sent: list[tuple[str, str]] = []

        def fake_call(requests, key, parallel):
            self.assertEqual(key, "redacted-test-key")
            self.assertEqual(parallel, 1)
            self.assertEqual(len(requests), 1)
            request = requests[0]
            self.assertEqual(
                request.row["extraction_case_id"], extract.LONGEVITY_ONECASE_ID
            )
            self.assertEqual(request.row["_longevity_onecase_contract"], "yes")
            sent.append((request.phase, request.row["extraction_case_id"]))
            value = longevity_response()
            return [
                extract.Result(
                    case_id=extract.LONGEVITY_ONECASE_ID,
                    status="success",
                    request_id=f"req_{request.phase}",
                    raw=json.dumps(value),
                    parsed=value,
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
            ]

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            for name in copied:
                shutil.copyfile(real_output / name, output / name)
            initial_stored = extract.load_new_case_checkpoint(output)
            initial_stored.pop(extract.LONGEVITY_ONECASE_ID, None)
            extract.write_new_case_checkpoint(output, initial_stored)
            selection_rows = extract.read_csv(
                output / "compensation_extraction_1000_selection_manifest.csv"
            )
            packet_map = {
                extract.LONGEVITY_ONECASE_ID: [packet()]
            }
            checkpoint_before = extract.sha_file(
                output / "compensation_extraction_1000_new_case_results.jsonl"
            )
            with mock.patch.object(extract, "call_gabriel", side_effect=fake_call):
                self.assertEqual(
                    extract.preflight_1000_longevity_onecase(
                        output, selection_rows, packet_map, "redacted-test-key"
                    ),
                    0,
                )
            self.assertEqual(
                extract.sha_file(
                    output / "compensation_extraction_1000_new_case_results.jsonl"
                ),
                checkpoint_before,
            )
            with (
                mock.patch.object(extract, "call_gabriel", side_effect=fake_call),
                mock.patch.object(
                    extract,
                    "materialize_cumulative_1000",
                    return_value={"decision": {"qa_pass": True}},
                ) as materialize,
            ):
                self.assertEqual(
                    extract.live_1000_longevity_onecase(
                        output,
                        selection_rows,
                        [],
                        packet_map,
                        extract.TARGETED_QA_500_DIR,
                        "redacted-test-key",
                    ),
                    0,
                )
            stored = extract.load_new_case_checkpoint(output)
            self.assertEqual(len(stored), 500)
            self.assertIn(extract.LONGEVITY_ONECASE_ID, stored)
            self.assertEqual(
                sent,
                [
                    ("preflight_1000_longevity_onecase", extract.LONGEVITY_ONECASE_ID),
                    ("live_1000_longevity_onecase", extract.LONGEVITY_ONECASE_ID),
                ],
            )
            materialize.assert_called_once()
            metadata = extract.read_csv(
                output / "compensation_extraction_1000_onecase_request_metadata.csv"
            )
            self.assertEqual(len(metadata), 2)
            self.assertEqual(
                {row["extraction_case_id"] for row in metadata},
                {extract.LONGEVITY_ONECASE_ID},
            )

    def test_cumulative_materialization_rejects_499_results(self) -> None:
        real_output = (
            ROOT
            / "docs/analysis/compensation_extraction"
            / "COMPENSATION-EVIDENCE-EXTRACTION-1000DOC-2026-07-25"
        )
        selection_rows = extract.read_csv(
            real_output / "compensation_extraction_1000_selection_manifest.csv"
        )
        stored = extract.load_new_case_checkpoint(real_output)
        stored.pop(extract.LONGEVITY_ONECASE_ID)
        self.assertEqual(len(stored), 499)
        with self.assertRaisesRegex(
            RuntimeError, "requires exactly 500 frozen new results"
        ):
            extract.materialize_cumulative_1000(
                real_output,
                selection_rows,
                [],
                stored,
                extract.TARGETED_QA_500_DIR,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
