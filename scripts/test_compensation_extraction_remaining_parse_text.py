#!/usr/bin/env python3
"""Offline regression tests for the remaining-readable parse-text extraction."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_compensation_evidence_extraction as base
import run_compensation_extraction_remaining_parse_text as remaining


def page(
    *, wage: int = 0, numeric: int = 0, table: int = 0, qual: int = 0,
    nonbase: int = 0, reference: bool = False
) -> base.PagePacket:
    return base.PagePacket(
        page=1,
        role="candidate",
        text="bounded",
        image="",
        wage=wage,
        numeric=numeric,
        table=table,
        qual=qual,
        nonbase=nonbase,
        reference=reference,
    )


class RemainingParseTextTests(unittest.TestCase):
    def test_cli_requires_exact_826(self) -> None:
        args = remaining.parse_args(
            ["--mode", "freeze_remaining_selection", "--output-dir", "/tmp/x"]
        )
        self.assertEqual(args.case_limit, 826)
        with self.assertRaises(ValueError):
            remaining.main(
                [
                    "--mode", "freeze_remaining_selection",
                    "--output-dir", "/tmp/x", "--case-limit", "825", "--dry-run",
                ]
            )

    def test_dry_run_never_calls_gabriel(self) -> None:
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(
            remaining, "freeze_selection", return_value=[]
        ), mock.patch.object(
            remaining, "freeze_packets", return_value=([], {})
        ), mock.patch.object(
            remaining, "write_freeze_outputs"
        ), mock.patch.object(base, "call_gabriel") as gabriel:
            result = remaining.main(
                [
                    "--mode", "freeze_remaining_selection",
                    "--output-dir", temp, "--dry-run",
                ]
            )
            self.assertEqual(result, 0)
            gabriel.assert_not_called()

    def test_active_prefers_targeted_qa_shadow_flag(self) -> None:
        self.assertFalse(
            remaining.active(
                {
                    "active_in_provisional_lane": "true",
                    "active_in_qa_corrected_lane": "false",
                }
            )
        )
        self.assertTrue(remaining.active({"active_in_provisional_lane": "true"}))

    def test_new_rows_preserve_provisional_provenance(self) -> None:
        source = {
            field: "" for field in base.QUANT_FIELDS
        }
        source.update(
            {
                "quantitative_observation_id": "qobs_x",
                "extraction_case_id": "cexrem_x",
                "qa_status": "provisional_unverified",
            }
        )
        row = remaining.new_cumulative_row(source, "quant")
        self.assertEqual(row["canonical_observation_id"], "qobs_x")
        self.assertEqual(row["cumulative_cohort"], "remaining_parse_text_826_new")
        self.assertEqual(row["active_in_qa_corrected_lane"], "true")

    def test_preflight_has_seven_unique_paths_including_duplicate(self) -> None:
        lanes = [
            "quantitative", "qualitative", "mixed", "non_base_wage",
            "reference_and_exclusion", "quantitative", "quantitative",
        ]
        rows = []
        packet_map = {}
        packets = [
            page(wage=8, numeric=8, table=5),
            page(wage=2, qual=8),
            page(wage=5, numeric=5, table=4, qual=5),
            page(nonbase=8, numeric=4),
            page(reference=True),
            page(wage=8, numeric=10, table=5),
            page(wage=3, numeric=3, table=2),
        ]
        for index, lane in enumerate(lanes):
            case_id = f"case_{index}"
            rows.append(
                {
                    "extraction_case_id": case_id,
                    "planned_lane": lane,
                    "inventory_rows_for_content_hash": "2" if index == 6 else "1",
                }
            )
            packet_map[case_id] = [packets[index]]
        chosen = remaining.choose_preflight(rows, packet_map)
        self.assertEqual(len(chosen), 7)
        self.assertEqual(len({row["extraction_case_id"] for _, row in chosen}), 7)
        self.assertEqual(chosen[0][0], "duplicate_hash_selection_provenance")

    def test_mixed_ready_still_requires_both_subrecord_families(self) -> None:
        value = {
            "case_disposition": "mixed_ready",
            "page_relationship": "exact_evidence_page",
            "quantitative_observations": [],
            "qualitative_observations": [],
            "non_base_wage_observations": [],
            "confidence": "high",
            "reason_codes": ["MIXED"],
            "short_rationale": "bounded",
        }
        with self.assertRaisesRegex(ValueError, "mixed_ready"):
            base.validate_response(json.dumps(value), {1})

    def test_nonbase_quantitative_item_fails_closed(self) -> None:
        value = {
            "case_disposition": "quantitative_ready",
            "page_relationship": "exact_evidence_page",
            "quantitative_observations": [
                {
                    "page_number": 1,
                    "compensation_type": "other",
                    "occupation_unit_classification_rank": "longevity",
                    "rate_value": "",
                    "salary_value": "",
                    "hourly_rate": "",
                    "annual_salary": "",
                    "pay_band": "",
                    "step": "",
                    "grade": "",
                    "percentage_increase": "",
                    "effective_date": "",
                    "currency_or_unit": "",
                    "confidence": "high",
                    "reason_code": "LONGEVITY_PAY",
                }
            ],
            "qualitative_observations": [],
            "non_base_wage_observations": [],
            "confidence": "high",
            "reason_codes": ["QUANT"],
            "short_rationale": "bounded",
        }
        with self.assertRaisesRegex(ValueError, "non-base compensation"):
            base.validate_response(json.dumps(value), {1})

    def test_materialization_refuses_partial_826(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "all 826"):
                remaining.materialize_cumulative(
                    Path(temp), [], [], {}, Path(temp)
                )

    def test_preflight_failure_does_not_create_live_scope(self) -> None:
        rows = [
            {
                "extraction_case_id": f"case_{index}",
                "planned_lane": lane,
                "inventory_rows_for_content_hash": "2" if index == 6 else "1",
            }
            for index, lane in enumerate(
                [
                    "quantitative", "qualitative", "mixed", "non_base_wage",
                    "reference_and_exclusion", "quantitative", "quantitative",
                ]
            )
        ]
        packet_map = {row["extraction_case_id"]: [page(wage=5, numeric=5, table=3, qual=3, nonbase=2, reference=True)] for row in rows}
        invalid = [
            base.Result(
                row["extraction_case_id"], "schema_invalid", "", "", None,
                0.1, 0, 0, 0, "ValueError", "invalid", "hash", 10, 0, 0,
            )
            for row in rows
        ]
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(
            base, "call_gabriel", return_value=invalid
        ):
            output = Path(temp)
            (output / "remaining_parse_text_selection_manifest.csv").write_text(
                "extraction_case_id\ncase_0\n", encoding="utf-8"
            )
            code = remaining.preflight(output, rows, packet_map, "redacted")
            self.assertEqual(code, 2)
            marker = json.loads(
                (output / ".remaining_preflight_passed.json").read_text()
            )
            self.assertFalse(marker["passed"])

    def test_runner_contains_no_url_or_download_workflow(self) -> None:
        source = Path(remaining.__file__).read_text(encoding="utf-8")
        self.assertNotIn("requests.get", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("pytesseract", source.lower())
        self.assertNotIn("ocrmypdf", source.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
