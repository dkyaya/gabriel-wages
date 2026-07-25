#!/usr/bin/env python3
"""Offline synthetic tests for provisional 500-document extraction lanes."""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_compensation_evidence_extraction.py"
spec = importlib.util.spec_from_file_location("compensation_extraction", RUNNER)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load compensation extraction runner")
extract = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = extract
spec.loader.exec_module(extract)


def valid_response(disposition: str = "mixed_ready") -> dict[str, object]:
    quantitative = [{
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
        "reason_code": "VISIBLE_SALARY",
    }]
    qualitative = [{
        "page_number": 2,
        "mechanism_type": "implementation_or_effective_date_logic",
        "bargaining_logic": "",
        "indexing_formula": "",
        "comparability_basis": "",
        "parity_logic": "",
        "step_progression_rule": "",
        "eligibility_rule": "",
        "implementation_rule": "The stated salary takes effect on the listed date.",
        "fiscal_constraint": "",
        "reopener_clause": "",
        "differentiation_logic": "Pay varies by step.",
        "confidence": "medium",
        "reason_code": "EFFECTIVE_DATE_RULE",
    }]
    nonbase = [{
        "page_number": 2,
        "non_base_wage_type": "stipend",
        "value_text": "$500",
        "effective_date": "",
        "eligibility_or_implementation_rule": "Eligible certified employees.",
        "confidence": "medium",
        "reason_code": "CERT_STIPEND",
    }]
    if disposition == "quantitative_ready":
        qualitative, nonbase = [], []
    elif disposition == "qualitative_ready":
        quantitative, nonbase = [], []
    elif disposition == "non_base_wage":
        quantitative, qualitative = [], []
    elif disposition in {"reference_only", "exclude", "second_review"}:
        quantitative, qualitative, nonbase = [], [], []
    return {
        "case_disposition": disposition,
        "page_relationship": "exact_evidence_page",
        "quantitative_observations": quantitative,
        "qualitative_observations": qualitative,
        "non_base_wage_observations": nonbase,
        "confidence": "high",
        "reason_codes": ["BOUNDED_EVIDENCE"],
        "short_rationale": "Bounded evidence supports provisional classification.",
    }


def selection_row(case_id: str, planned_lane: str) -> dict[str, str]:
    row = {field: "" for field in extract.SELECTION_FIELDS}
    row.update({
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
        "contract_period_start": "2025",
        "contract_period_end": "2027",
        "content_artifact_path": "local.pdf",
        "content_hash": case_id,
        "pdf_page_count": "2",
        "candidate_wage_pages": "2",
        "planned_lane": planned_lane,
    })
    return row


class CompensationExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_strict_schema_accepts_each_lane_and_fails_closed(self) -> None:
        for disposition in extract.DISPOSITIONS:
            parsed = extract.validate_response(
                json.dumps(valid_response(disposition)), {2}
            )
            self.assertEqual(parsed["case_disposition"], disposition)
        bad = valid_response()
        bad["undeclared"] = "not allowed"
        with self.assertRaises(ValueError):
            extract.validate_response(json.dumps(bad), {2})
        bad = valid_response()
        bad["quantitative_observations"][0]["page_number"] = 99
        with self.assertRaises(ValueError):
            extract.validate_response(json.dumps(bad), {2})
        bad = valid_response()
        bad["qualitative_observations"][0]["bargaining_logic"] = "x" * 241
        with self.assertRaises(ValueError):
            extract.validate_response(json.dumps(bad), {2})

    def test_packet_caps_and_no_complete_page_text_saved(self) -> None:
        pdf = self.root / "packet.pdf"
        doc = canvas.Canvas(str(pdf), pagesize=(612, 792))
        for page in range(1, 9):
            for line in range(80):
                doc.drawString(
                    30,
                    770 - line * 9,
                    f"Page {page} line {line} salary step rate 50000 effective CPI",
                )
            doc.showPage()
        doc.save()
        row = selection_row("case_packet", "mixed")
        row.update({
            "content_artifact_path": str(pdf),
            "pdf_page_count": "8",
            "candidate_wage_pages": "2,4,6",
        })
        pages = extract.build_packet(row, {})
        self.assertLessEqual(len(pages), 6)
        self.assertLessEqual(sum(len(page.text) for page in pages), 6000)
        self.assertTrue(all(len(page.text) <= 1500 for page in pages))
        packet_rows, _ = extract.freeze_packets(self.root / "packet_out", [row])
        manifest = (self.root / "packet_out/compensation_extraction_500_packet_manifest.csv").read_text()
        self.assertNotIn("salary step rate 50000 effective CPI", manifest)
        self.assertTrue(all("bounded_evidence_pointer" in item for item in packet_rows))

    def test_exact_500_matched_selection_is_deterministic(self) -> None:
        eligible = []
        for index in range(200):
            state = f"S{index % 40:02d}"
            municipality = f"Town {index:03d}"
            units = ["non_safety", "police"] + (["fire"] if index < 120 else [])
            for unit in units:
                key = f"{state}-{municipality}-{unit}"
                eligible.append({
                    "state": state,
                    "municipality": municipality,
                    "unit_type": unit,
                    "content_hash": key,
                    "text_table_detection_id": f"ttd-{key}",
                    "pdf_readiness_id": f"pr-{key}",
                    "source_review_id": f"sr-{key}",
                    "candidate_queue_row_id": f"cq-{key}",
                    "triage_id": f"tr-{key}",
                    "verification_id": f"vr-{key}",
                    "government_name": municipality,
                    "candidate_source_type": "cba",
                    "content_artifact_path": f"{key}.pdf",
                    "pdf_page_count": "3",
                    "text_layer_status": "present",
                    "wage_table_signal": "likely",
                    "extraction_pilot_priority": "p1",
                    "candidate_wage_pages": "2",
                    "_score": 50.0,
                    "_source": {
                        "contract_or_document_period_start": "2025",
                        "contract_or_document_period_end": "2027",
                    },
                    "_gate3": {},
                })
        with mock.patch.object(extract, "load_inputs", return_value=(eligible, {})):
            first = extract.freeze_selection(Path("unused"), self.root / "first", 500)
            second = extract.freeze_selection(Path("unused"), self.root / "second", 500)
        self.assertEqual([row["document_identity_id"] for row in first], [row["document_identity_id"] for row in second])
        self.assertEqual(len(first), 500)
        self.assertEqual(len({row["document_identity_id"] for row in first}), 500)
        self.assertEqual(
            {unit: sum(row["unit_type"] == unit for row in first) for unit in ("police", "fire", "non_safety")},
            {"police": 180, "fire": 120, "non_safety": 200},
        )
        self.assertTrue(all(row["matched_non_safety_case_id"] for row in first))

    def test_mixed_lane_preserves_separate_subrecords_and_join_key(self) -> None:
        row = selection_row("case_mixed", "mixed")
        result = valid_response("mixed_ready")
        lanes = extract.materialize_lanes(self.root / "out", [row], {"case_mixed": result})
        self.assertEqual(len(lanes["rows"]["quant"]), 1)
        self.assertEqual(len(lanes["rows"]["qual"]), 1)
        self.assertEqual(len(lanes["rows"]["mixed"]), 1)
        join = lanes["rows"]["mixed"][0]["mixed_join_key"]
        self.assertEqual(lanes["rows"]["quant"][0]["mixed_join_key"], join)
        self.assertEqual(lanes["rows"]["qual"][0]["mixed_join_key"], join)

    def test_non_base_wage_never_silently_promoted(self) -> None:
        row = selection_row("case_nonbase", "non_base_wage")
        lanes = extract.materialize_lanes(
            self.root / "out", [row], {"case_nonbase": valid_response("non_base_wage")}
        )
        self.assertEqual(lanes["rows"]["quant"], [])
        self.assertEqual(len(lanes["rows"]["nonbase"]), 1)

    def test_qa_distinguishes_steps_from_conflicts_and_flags_nonbase(self) -> None:
        row = selection_row("case_qa", "quantitative")
        result = valid_response("quantitative_ready")
        base = dict(result["quantitative_observations"][0])
        step_two = dict(base, step="2", salary_value="52000", annual_salary="52000")
        true_conflict = dict(base, salary_value="51000", annual_salary="51000")
        overtime = dict(
            base,
            compensation_type="other",
            occupation_unit_classification_rank="",
            salary_value="",
            annual_salary="",
            step="",
            rate_value="1.5 times regular rate",
            currency_or_unit="overtime multiplier",
            reason_code="OVERTIME_RATE",
        )
        result["quantitative_observations"] = [base, step_two, true_conflict, overtime]
        lanes = extract.materialize_lanes(
            self.root / "out", [row], {"case_qa": result}
        )
        packet = [{
            "extraction_case_id": "case_qa", "page_number": "2",
            "packet_page_count": "1", "packet_text_chars": "100",
            "text_chars": "100",
        }]
        decision = extract.qa_and_decision(
            self.root / "out", [row], packet, {"case_qa": result}, lanes
        )
        self.assertEqual(decision["conflicting_quantitative_group_count"], 1)
        self.assertEqual(decision["quantitative_records_flagged_possible_non_base_wage"], 1)
        statuses = [item["qa_status"] for item in lanes["rows"]["quant"]]
        self.assertIn("needs_conflict_review", statuses)
        self.assertIn("needs_non_base_wage_review", statuses)

    def test_representative_preflight_uses_four_paths_and_no_raw_artifacts(self) -> None:
        rows = [selection_row(f"case_{lane}", lane) for lane in (
            "quantitative", "qualitative", "mixed", "reference_and_exclusion"
        )]
        packets = {
            row["extraction_case_id"]: [extract.PagePacket(2, "candidate", "bounded", "", 1, 1, 0, 0, 0, False)]
            for row in rows
        }
        fake_results = []
        for row in rows:
            parsed = valid_response("reference_only")
            raw = json.dumps(parsed)
            fake_results.append(extract.Result(
                row["extraction_case_id"], "success", f"req_{row['extraction_case_id']}",
                raw, parsed, 0.01, 1, 1, 2, "", "", "hash", 100, 0, 0,
            ))
        with mock.patch.object(extract, "call_gabriel", return_value=fake_results) as call:
            self.assertEqual(extract.preflight(self.root / "out", rows, packets, "secret"), 0)
        self.assertEqual(len(call.call_args.args[0]), 4)
        names = {path.name for path in (self.root / "out").rglob("*") if path.is_file()}
        self.assertFalse(any("raw_prompt" in name or "raw_response" in name for name in names))
        with (self.root / "out/compensation_extraction_request_metadata.csv").open() as handle:
            metadata = list(csv.DictReader(handle))
        self.assertTrue(all(row["raw_prompt_saved"] == "false" and row["raw_response_saved"] == "false" for row in metadata))
        self.assertTrue(all(row["credential_value_saved"] == "false" for row in metadata))

    def test_bad_preflight_schema_fails_closed(self) -> None:
        rows = [selection_row(f"case_{lane}", lane) for lane in (
            "quantitative", "qualitative", "mixed", "reference_and_exclusion"
        )]
        packets = {row["extraction_case_id"]: [extract.PagePacket(2, "candidate", "x", "", 0, 0, 0, 0, 0, False)] for row in rows}
        failed = [extract.Result(row["extraction_case_id"], "schema_invalid", "", "{}", None, 0.01, 0, 0, 0, "ValueError", "invalid schema", "hash", 2, 0, 0) for row in rows]
        with mock.patch.object(extract, "call_gabriel", return_value=failed):
            self.assertEqual(extract.preflight(self.root / "out", rows, packets, "secret"), 2)
        marker = json.loads((self.root / "out/.preflight_passed.json").read_text())
        self.assertFalse(marker["passed"])

    def test_primary_prompt_is_bounded_and_blind_to_prior_labels(self) -> None:
        row = selection_row("case_prompt", "quantitative")
        row.update({"gate3_category": "must_not_be_sent", "gate3_confidence": "high"})
        pages = [extract.PagePacket(2, "candidate", "Salary 50000", "", 1, 1, 1, 0, 0, False)]
        payload = extract.prompt(row, pages)
        for forbidden in ("gate3_category", "gate3_confidence", "REVIEW1", "REVIEW2", "Gate 1", "Gate 2"):
            self.assertNotIn(forbidden, payload)
        self.assertLessEqual(sum(len(page.text) for page in pages), 6000)

    def test_live_requires_passed_preflight_and_explicit_resume(self) -> None:
        row = selection_row("case_live", "quantitative")
        with self.assertRaises(FileNotFoundError):
            extract.live(self.root / "out", [row], [], {"case_live": []}, "secret", True)
        with self.assertRaises(FileNotFoundError):
            extract.main(["--mode", "live_lanes", "--output-dir", str(self.root / "out"), "--allow-gabriel"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
