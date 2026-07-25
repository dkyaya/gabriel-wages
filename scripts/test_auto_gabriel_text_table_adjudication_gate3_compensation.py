#!/usr/bin/env python3
"""Offline synthetic tests for Gate 3 compensation-evidence adjudication."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_auto_gabriel_text_table_adjudication.py"
spec = importlib.util.spec_from_file_location("auto_gabriel_gate3", RUNNER)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load automated adjudication runner")
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def valid_gate3(**overrides: object) -> str:
    payload: dict[str, object] = {
        "compensation_evidence_category": "quant_table_ready",
        "quantitative_evidence_present": "yes",
        "qualitative_mechanism_evidence_present": "no",
        "quantitative_evidence_type": "salary_schedule",
        "qualitative_mechanism_type": "none",
        "non_wage_compensation_type": "not_applicable",
        "extractable_quant_fields": ["salary", "rank", "effective_date"],
        "extractable_qual_fields": [],
        "candidate_page_relationship": "exact_evidence_page",
        "evidence_strength": "high",
        "extraction_path_recommendation": "quantitative_extraction_ready",
        "gate3_confidence": "high",
        "gate3_reason_codes": ["QUANT_SCHEDULE"],
        "gate3_short_rationale": "A bounded salary schedule maps ranks to pay.",
        "vision_legibility": "not_applicable",
        "image_table_structure_observed": "not_applicable",
        "image_role_pay_alignment_observed": "not_applicable",
    }
    payload.update(overrides)
    return json.dumps(payload)


class Gate3CompensationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pdf = self.root / "bounded.pdf"
        document = canvas.Canvas(str(self.pdf), pagesize=(612, 792))
        page_text = [
            "Agreement front matter",
            "Salary Schedule Rank Step Annual Salary 50000",
            "Effective July 1 employees receive a 3 percent increase",
            "Wages follow CPI COLA and comparability study rules",
            "Health insurance contribution benefits table",
            "Table of Contents Salary Appendix 8",
            "Grievance and discipline procedure",
            "Compact Officer pay band listing 50000",
        ]
        for text in page_text:
            document.drawString(40, 740, text)
            document.showPage()
        document.save()
        self.image = self.root / "page_0002.jpg"
        Image.new("RGB", (200, 260), color="white").save(self.image)
        self.input = self.root / "blinded.csv"
        self.manifest = self.root / "manifest.csv"
        self.output = self.root / "out"
        self.row = {
            "adjudication_case_id": "adj_gate3",
            "calibration_id": "cal_gate3",
            "source_review_id": "sr_gate3",
            "pdf_readiness_id": "pr_gate3",
            "candidate_queue_row_id": "queue_gate3",
            "state": "ZZ",
            "municipality": "Testville",
            "government_name": "City of Testville",
            "unit_type": "police",
            "candidate_source_type": "cba",
            "pdf_page_count": "8",
            "blinded_candidate_pages": "2",
            "blinded_nearby_pages": "1,3",
            "blinded_navigation_pages": "6",
            "content_artifact_path": str(self.pdf),
        }
        write_csv(self.input, list(self.row), [self.row])
        manifest_row = {
            "adjudication_case_id": "adj_gate3",
            "calibration_id": "cal_gate3",
            "page_number": "2",
            "page_role": "candidate",
            "rendered_image_path": str(self.image),
            "render_status": "rendered",
            "rendered_bytes": str(self.image.stat().st_size),
            "rendered_sha256": digest(self.image),
        }
        write_csv(self.manifest, list(manifest_row), [manifest_row])
        self.input_hash = digest(self.input)
        self.manifest_hash = digest(self.manifest)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def args(self, *extra: str) -> list[str]:
        return [
            "--blinded-input-csv",
            str(self.input),
            "--render-manifest-csv",
            str(self.manifest),
            "--output-dir",
            str(self.output),
            "--gate-id",
            "SYNTHETIC-GATE3",
            "--gate-mode",
            gate.GATE3_MODE,
            "--candidate-page-window",
            "1",
            "--navigation-page-budget",
            "4",
            "--max-pages-per-case",
            "6",
            "--max-text-chars-per-page",
            "1500",
            "--max-text-chars-per-case",
            "6000",
            "--compensation-schema-version",
            gate.GATE3_SCHEMA_VERSION,
            "--no-save-full-text",
            *extra,
        ]

    def evidence(self, *, use_images: bool = False) -> object:
        render_map = gate.validate_render_manifest(self.manifest, [self.row])
        return gate.build_case_evidence(
            self.row,
            gate_id="SYNTHETIC-GATE3",
            render_map=render_map["adj_gate3"],
            max_pages=6,
            navigation_budget=4,
            max_chars_per_page=1500,
            max_chars_per_case=6000,
            gate_mode=gate.GATE3_MODE,
            candidate_window=1,
            use_images=use_images,
            max_images=6,
            max_image_bytes=2_000_000,
        )

    def adjudicate(self, response: str) -> dict[str, str]:
        result = gate.LiveResult(
            request_id="req_synthetic",
            status="success",
            response_text=response,
            elapsed_seconds=0.1,
            input_tokens=10,
            output_tokens=10,
            total_tokens=20,
            error_type="",
            error_message="",
        )
        fields, _, failed = gate.gate3_fields_from_result(
            evidence=self.evidence(),
            result=result,
            backend=gate.DEFAULT_BACKEND,
            model=gate.DEFAULT_MODEL,
        )
        self.assertIsNone(failed)
        return fields

    def test_gate1_and_gate2_modes_remain_available(self) -> None:
        self.assertIn(gate.GATE1_MODE, gate.GATE_MODES)
        self.assertIn(gate.GATE2_MODE, gate.GATE_MODES)
        parsed = gate.parse_args(
            [
                "--blinded-input-csv",
                str(self.input),
                "--render-manifest-csv",
                str(self.manifest),
                "--output-dir",
                str(self.output),
                "--gate-id",
                "OLD-MODE",
            ]
        )
        self.assertEqual(parsed.gate_mode, gate.GATE1_MODE)

    def test_dry_run_sends_no_request_and_writes_no_sensitive_artifacts(self) -> None:
        with mock.patch.object(
            gate,
            "run_live_requests",
            side_effect=AssertionError("dry-run sent a request"),
        ):
            self.assertEqual(
                gate.main(
                    self.args(
                        "--dry-run",
                        "--use-rendered-images",
                        "--allow-image-fallback-to-text-layout",
                    )
                ),
                0,
            )
        names = {path.name for path in self.output.rglob("*") if path.is_file()}
        self.assertFalse(any("raw_prompt" in name for name in names))
        self.assertFalse(any("raw_response" in name for name in names))
        summary = json.loads(
            (
                self.output / "auto_gabriel_compensation_adjudication_summary.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(summary["status"], "dry_run_completed_no_gabriel_calls")
        self.assertTrue(summary["image_evidence_used"])

    def test_primary_payload_excludes_all_prior_labels_and_respects_caps(self) -> None:
        evidence = self.evidence(use_images=True)
        for marker in (
            "REVIEW1",
            "REVIEW2",
            "GATE1",
            "GATE2",
            "auto_gate_label",
            "wage_schedule_table_confirmed_label",
        ):
            self.assertNotIn(marker, evidence.prompt)
        self.assertLessEqual(len(evidence.pages), 6)
        self.assertLessEqual(evidence.text_chars, 6000)
        self.assertTrue(all(page.snippet_chars <= 1500 for page in evidence.pages))
        self.assertLessEqual(len(evidence.image_paths or []), 6)

    def test_quant_table_and_compact_categories(self) -> None:
        table = self.adjudicate(valid_gate3())
        self.assertEqual(table["compensation_evidence_category"], "quant_table_ready")
        compact = self.adjudicate(
            valid_gate3(
                compensation_evidence_category="quant_compact_ready",
                quantitative_evidence_type="compact_compensation_sheet",
                extraction_path_recommendation="extraction_ready_with_schema_update",
            )
        )
        self.assertEqual(compact["compensation_evidence_category"], "quant_compact_ready")

    def test_quant_prose_and_qual_mechanism_categories(self) -> None:
        quant = self.adjudicate(
            valid_gate3(
                compensation_evidence_category="quant_prose_ready",
                quantitative_evidence_type="prose_percentage_raise",
                extractable_quant_fields=["percentage_increase", "effective_date"],
            )
        )
        self.assertEqual(quant["compensation_evidence_category"], "quant_prose_ready")
        qual = self.adjudicate(
            valid_gate3(
                compensation_evidence_category="qual_mechanism_ready",
                quantitative_evidence_present="no",
                qualitative_mechanism_evidence_present="yes",
                quantitative_evidence_type="none",
                qualitative_mechanism_type="CPI_or_COLA_indexing",
                extractable_quant_fields=[],
                extractable_qual_fields=["mechanism", "indexing_formula"],
                extraction_path_recommendation="qualitative_extraction_ready",
            )
        )
        self.assertEqual(qual["compensation_evidence_category"], "qual_mechanism_ready")

    def test_mixed_nonwage_reference_and_irrelevant_categories(self) -> None:
        cases = [
            (
                "mixed_quant_qual_ready",
                dict(
                    qualitative_mechanism_evidence_present="yes",
                    qualitative_mechanism_type="step_movement_or_seniority",
                    extractable_qual_fields=["step_progression_rule"],
                    extraction_path_recommendation="mixed_extraction_ready",
                ),
            ),
            (
                "non_wage_compensation",
                dict(
                    quantitative_evidence_present="no",
                    quantitative_evidence_type="none",
                    non_wage_compensation_type="benefits",
                    extractable_quant_fields=[],
                    extraction_path_recommendation="exclude_for_now",
                ),
            ),
            (
                "reference_navigation_only",
                dict(
                    quantitative_evidence_present="no",
                    quantitative_evidence_type="none",
                    candidate_page_relationship="points_to_later_evidence",
                    extractable_quant_fields=[],
                    extraction_path_recommendation="reference_followup_needed",
                ),
            ),
            (
                "not_compensation_relevant",
                dict(
                    quantitative_evidence_present="no",
                    quantitative_evidence_type="none",
                    extractable_quant_fields=[],
                    extraction_path_recommendation="exclude_for_now",
                ),
            ),
        ]
        for category, overrides in cases:
            with self.subTest(category=category):
                fields = self.adjudicate(
                    valid_gate3(compensation_evidence_category=category, **overrides)
                )
                self.assertEqual(fields["compensation_evidence_category"], category)

    def test_bad_json_fails_closed(self) -> None:
        result = gate.LiveResult(
            request_id="bad",
            status="success",
            response_text="not-json",
            elapsed_seconds=0.1,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            error_type="",
            error_message="",
        )
        fields, _, failed = gate.gate3_fields_from_result(
            evidence=self.evidence(),
            result=result,
            backend=gate.DEFAULT_BACKEND,
            model=gate.DEFAULT_MODEL,
        )
        self.assertIsNotNone(failed)
        self.assertEqual(fields["compensation_evidence_category"], "error")
        self.assertEqual(fields["extraction_path_recommendation"], "error")

    def test_inputs_unmodified_and_image_fallback_is_explicit(self) -> None:
        self.assertEqual(digest(self.input), self.input_hash)
        self.assertEqual(digest(self.manifest), self.manifest_hash)

    def test_vision_preflight_can_fall_back_to_text_layout(self) -> None:
        failed = gate.LiveResult(
            request_id="",
            status="request_failed",
            response_text="",
            elapsed_seconds=0.1,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            error_type="BadRequestError",
            error_message="input_image unsupported",
        )
        passed = gate.LiveResult(
            request_id="req_text_fallback",
            status="success",
            response_text=valid_gate3(),
            elapsed_seconds=0.1,
            input_tokens=10,
            output_tokens=10,
            total_tokens=20,
            error_type="",
            error_message="",
        )
        fallback_output = self.root / "fallback"
        args = self.args(
            "--vision-preflight-only",
            "--allow-gabriel",
            "--use-rendered-images",
            "--allow-image-fallback-to-text-layout",
        )
        args[args.index(str(self.output))] = str(fallback_output)
        with (
            mock.patch.object(
                gate, "load_subscription_key", return_value=("configured", "test")
            ),
            mock.patch.object(
                gate, "run_live_requests", side_effect=[[failed], [passed]]
            ) as transport,
        ):
            self.assertEqual(gate.main(args), 0)
        self.assertEqual(transport.call_count, 2)
        summary = json.loads(
            (
                fallback_output
                / "auto_gabriel_compensation_adjudication_summary.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(summary["image_fallback_occurred"])
        self.assertFalse(summary["image_evidence_used"])
        fields = gate.empty_gate3(
            backend=gate.DEFAULT_BACKEND,
            model=gate.DEFAULT_MODEL,
            status="not_called",
            used_images=False,
        )
        self.assertEqual(fields["vision_evidence_used"], "false")
        self.assertEqual(fields["vision_legibility"], "not_applicable")
        self.assertEqual(digest(self.input), self.input_hash)
        self.assertEqual(digest(self.manifest), self.manifest_hash)


if __name__ == "__main__":
    unittest.main(verbosity=2)
