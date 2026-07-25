#!/usr/bin/env python3
"""Offline synthetic tests for the automated GABRIEL adjudication gate."""

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


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT / "scripts" / "run_auto_gabriel_text_table_adjudication.py"
)
SCHEMA_PATH = (
    REPO_ROOT
    / "docs/analysis/text_table_auto_gabriel_adjudication_schema_2026-07-24.md"
)

spec = importlib.util.spec_from_file_location("auto_gabriel_gate", SCRIPT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load automated adjudication runner")
gate = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate
spec.loader.exec_module(gate)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(
    path: Path, fieldnames: list[str], rows: list[dict[str, str]]
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def valid_response(**overrides: object) -> str:
    result: dict[str, object] = {
        "wage_schedule_present": "no",
        "candidate_page_relationship": "wrong_page",
        "visual_table_type": "prose_only",
        "non_wage_family": "memorandum_without_table",
        "navigation_needed": "no",
        "navigation_target_found": "not_applicable",
        "extraction_complexity": "not_extractable",
        "extraction_recommendation": "exclude_for_now",
        "confidence": "high",
        "reason_codes": ["PROSE_ONLY"],
        "short_rationale": "The bounded page contains prose, not a pay table.",
    }
    result.update(overrides)
    return json.dumps(result)


class AutomatedGabrielGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.input_path = self.root / "blinded.csv"
        self.manifest_path = self.root / "render_manifest.csv"
        self.output_dir = self.root / "output"
        self.pdf_paths: list[Path] = []
        input_rows: list[dict[str, str]] = []
        manifest_rows: list[dict[str, str]] = []
        for index in range(2):
            pdf_path = self.root / f"case_{index}.pdf"
            pdf = canvas.Canvas(str(pdf_path), pagesize=(612, 792))
            for page_number in range(1, 8):
                if page_number == 2:
                    pdf.drawString(
                        50,
                        740,
                        "Salary Schedule Classification Step Annual Rate",
                    )
                    for row_number in range(8):
                        pdf.drawString(
                            50,
                            710 - row_number * 22,
                            f"Officer Step {row_number + 1} 50000",
                        )
                elif page_number == 4:
                    pdf.drawString(
                        50, 740, "Table of Contents Salary Schedule 6"
                    )
                elif page_number == 6:
                    pdf.drawString(
                        50, 740, "Classification Hourly Rate Annual Salary"
                    )
                else:
                    pdf.drawString(50, 740, "Agreement narrative page")
                pdf.showPage()
            pdf.save()
            self.pdf_paths.append(pdf_path)

            image_path = self.root / f"case_{index}_page_2.jpg"
            Image.new("L", (300, 400), color=245).save(
                image_path, format="JPEG"
            )
            input_rows.append(
                {
                    "adjudication_case_id": f"adj_{index}",
                    "calibration_id": f"cal_{index}",
                    "source_review_id": f"sr_{index}",
                    "pdf_readiness_id": f"pr_{index}",
                    "candidate_queue_row_id": f"queue_{index}",
                    "state": "ZZ",
                    "municipality": f"Town {index}",
                    "government_name": f"City of Town {index}",
                    "unit_type": "police" if index == 0 else "fire",
                    "candidate_source_type": "cba",
                    "pdf_page_count": "7",
                    "blinded_candidate_pages": "2",
                    "blinded_nearby_pages": "1,3",
                    "blinded_navigation_pages": "4",
                    "content_artifact_path": str(pdf_path),
                }
            )
            manifest_rows.append(
                {
                    "adjudication_case_id": f"adj_{index}",
                    "calibration_id": f"cal_{index}",
                    "page_number": "2",
                    "page_role": "candidate",
                    "rendered_image_path": image_path.name,
                    "render_status": "rendered",
                    "rendered_bytes": str(image_path.stat().st_size),
                    "rendered_sha256": digest(image_path),
                }
            )
        write_csv(
            self.input_path,
            [
                "adjudication_case_id",
                "calibration_id",
                "source_review_id",
                "pdf_readiness_id",
                "candidate_queue_row_id",
                "state",
                "municipality",
                "government_name",
                "unit_type",
                "candidate_source_type",
                "pdf_page_count",
                "blinded_candidate_pages",
                "blinded_nearby_pages",
                "blinded_navigation_pages",
                "content_artifact_path",
            ],
            input_rows,
        )
        write_csv(
            self.manifest_path,
            [
                "adjudication_case_id",
                "calibration_id",
                "page_number",
                "page_role",
                "rendered_image_path",
                "render_status",
                "rendered_bytes",
                "rendered_sha256",
            ],
            manifest_rows,
        )
        self.input_hash = digest(self.input_path)
        self.manifest_hash = digest(self.manifest_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def base_args(self, output_dir: Path) -> list[str]:
        return [
            "--blinded-input-csv",
            str(self.input_path),
            "--render-manifest-csv",
            str(self.manifest_path),
            "--output-dir",
            str(output_dir),
            "--gate-id",
            "SYNTHETIC-GATE",
            "--candidate-page-window",
            "1",
            "--navigation-page-budget",
            "2",
            "--max-pages-per-case",
            "4",
            "--max-text-chars-per-page",
            "200",
            "--max-text-chars-per-case",
            "600",
            "--no-save-full-text",
        ]

    def make_evidence(
        self,
        *,
        table: float,
        wage: float,
        numeric: float,
        non_wage: float,
        compact: float = 0.0,
        targets: list[int] | None = None,
    ) -> object:
        page = gate.PageEvidence(
            page_number=2,
            role="candidate",
            snippet="[NUM] redacted bounded evidence",
            snippet_chars=31,
            wage_terms=4,
            role_terms=4,
            numeric_tokens=8,
            money_tokens=4,
            percent_tokens=0,
            row_like_lines=7,
            column_lines=7,
            header_lines=2,
            geometry_rows=7,
            geometry_columns=4,
            benefit_terms=0,
            budget_terms=0,
            classification_terms=2,
            index_signal=False,
            front_signal=False,
            rendered_available=True,
            image_horizontal_bands=8,
            image_vertical_bands=4,
            image_dark_density=0.1,
            navigation_targets=[],
        )
        source = {
            "adjudication_case_id": "adj",
            "calibration_id": "cal",
            "source_review_id": "sr",
            "pdf_readiness_id": "pr",
            "candidate_queue_row_id": "queue",
            "state": "ZZ",
            "municipality": "Town",
            "government_name": "City of Town",
            "unit_type": "police",
            "candidate_source_type": "cba",
            "pdf_page_count": "7",
            "content_artifact_path": str(self.pdf_paths[0]),
        }
        return gate.CaseEvidence(
            source=source,
            auto_id="auto",
            pages=[page],
            candidate_pages=[2],
            nearby_pages=[],
            navigation_pages=[],
            text_chars=31,
            table_score=table,
            wage_score=wage,
            numeric_score=numeric,
            navigation_score=0.0,
            non_wage_score=non_wage,
            compact_score=compact,
            navigation_targets_found=targets or [],
            prompt="synthetic",
        )

    def gabriel_fields(self, **overrides: str) -> dict[str, str]:
        fields = gate.empty_gabriel(
            backend=gate.DEFAULT_BACKEND,
            model=gate.DEFAULT_MODEL,
            status="success",
        )
        fields.update(
            {
                "gabriel_schema_valid": "true",
                "gabriel_wage_schedule_present": "yes",
                "gabriel_candidate_page_relationship": "exact_table_page",
                "gabriel_visual_table_type": "classification_pay_table",
                "gabriel_non_wage_family": "not_applicable",
                "gabriel_navigation_needed": "no",
                "gabriel_navigation_target_found": "not_applicable",
                "gabriel_extraction_complexity": "easy",
                "gabriel_extraction_recommendation": "extraction_ready",
                "gabriel_confidence": "high",
            }
        )
        fields.update(overrides)
        return fields

    def test_dry_run_sends_no_gabriel_requests_and_respects_max_cases(
        self,
    ) -> None:
        args = self.base_args(self.output_dir) + [
            "--dry-run",
            "--max-cases",
            "1",
        ]
        with mock.patch.object(
            gate,
            "run_live_requests",
            side_effect=AssertionError("network path must not run"),
        ):
            self.assertEqual(gate.main(args), 0)
        with (
            self.output_dir / "auto_gabriel_adjudication_ledger.csv"
        ).open(newline="", encoding="utf-8") as handle:
            ledger = list(csv.DictReader(handle))
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["gabriel_status"], "not_called")

    def test_preflight_accepts_strict_mocked_json(self) -> None:
        result = gate.LiveResult(
            request_id="req_mock",
            status="success",
            response_text=valid_response(),
            elapsed_seconds=0.01,
            input_tokens=10,
            output_tokens=10,
            total_tokens=20,
            error_type="",
            error_message="",
        )
        with (
            mock.patch.object(
                gate, "load_subscription_key", return_value=("fake", "test")
            ),
            mock.patch.object(gate, "run_live_requests", return_value=[result]),
        ):
            code = gate.main(
                self.base_args(self.output_dir)
                + ["--preflight-only", "--allow-gabriel"]
            )
        self.assertEqual(code, 0)
        summary = json.loads(
            (
                self.output_dir / "auto_gabriel_adjudication_summary.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            summary["decision"]["gabriel_schema_valid_rate"], 1.0
        )

    def test_bad_gabriel_json_fails_closed(self) -> None:
        evidence = self.make_evidence(
            table=0.9, wage=0.9, numeric=0.9, non_wage=0.0
        )
        result = gate.LiveResult(
            request_id="req_bad",
            status="success",
            response_text="{not-json",
            elapsed_seconds=0.01,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            error_type="",
            error_message="",
        )
        fields, _, failed = gate.gabriel_fields_from_result(
            evidence=evidence,
            result=result,
            backend=gate.DEFAULT_BACKEND,
            model=gate.DEFAULT_MODEL,
        )
        self.assertIsNotNone(failed)
        self.assertEqual(fields["gabriel_schema_valid"], "false")
        self.assertEqual(
            gate.combine_gate(evidence, fields)["auto_gate_label"], "error"
        )

    def test_missing_credentials_fails_clearly_without_request(self) -> None:
        with (
            mock.patch.object(
                gate, "load_subscription_key", return_value=(None, "none")
            ),
            mock.patch.object(
                gate,
                "run_live_requests",
                side_effect=AssertionError("request must not run"),
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError, "HARVARD_SUBSCRIPTION_KEY is unavailable"
            ):
                gate.main(
                    self.base_args(self.output_dir)
                    + ["--preflight-only", "--allow-gabriel"]
                )

    def test_wage_prose_cannot_be_high_confidence(self) -> None:
        evidence = self.make_evidence(
            table=0.1, wage=0.9, numeric=0.1, non_wage=0.2
        )
        fields = self.gabriel_fields(
            gabriel_visual_table_type="prose_only",
            gabriel_wage_schedule_present="no",
            gabriel_extraction_recommendation="exclude_for_now",
        )
        self.assertNotEqual(
            gate.combine_gate(evidence, fields)["auto_gate_label"],
            "extraction_ready_high_confidence",
        )

    def test_benefits_table_cannot_be_high_confidence(self) -> None:
        evidence = self.make_evidence(
            table=0.9, wage=0.6, numeric=0.9, non_wage=0.9
        )
        fields = self.gabriel_fields(
            gabriel_visual_table_type="benefits_table",
            gabriel_non_wage_family="benefits",
            gabriel_wage_schedule_present="no",
            gabriel_extraction_recommendation="exclude_for_now",
        )
        self.assertEqual(
            gate.combine_gate(evidence, fields)["auto_gate_label"],
            "exclude_for_now",
        )

    def test_classification_without_pay_cannot_be_high_confidence(self) -> None:
        evidence = self.make_evidence(
            table=0.8, wage=0.2, numeric=0.1, non_wage=0.8
        )
        fields = self.gabriel_fields(
            gabriel_visual_table_type="classification_without_pay",
            gabriel_non_wage_family="classification_without_pay",
            gabriel_wage_schedule_present="no",
            gabriel_extraction_recommendation="exclude_for_now",
        )
        self.assertEqual(
            gate.combine_gate(evidence, fields)["auto_gate_label"],
            "exclude_for_now",
        )

    def test_strong_confirmed_wage_table_can_be_high_confidence(self) -> None:
        evidence = self.make_evidence(
            table=0.9, wage=0.8, numeric=0.8, non_wage=0.1
        )
        self.assertEqual(
            gate.combine_gate(
                evidence, self.gabriel_fields()
            )["auto_gate_label"],
            "extraction_ready_high_confidence",
        )

    def test_contents_navigation_is_not_high_without_target_evidence(
        self,
    ) -> None:
        evidence = self.make_evidence(
            table=0.2, wage=0.5, numeric=0.2, non_wage=0.7
        )
        fields = self.gabriel_fields(
            gabriel_candidate_page_relationship="points_to_later_table",
            gabriel_visual_table_type="index_or_contents",
            gabriel_non_wage_family="index_or_contents",
            gabriel_navigation_needed="yes",
            gabriel_navigation_target_found="no",
            gabriel_extraction_recommendation="second_review_required",
        )
        self.assertEqual(
            gate.combine_gate(evidence, fields)["auto_gate_label"],
            "second_review_required",
        )

    def test_page_and_text_budgets_are_enforced(self) -> None:
        _, rows = gate.read_csv(self.input_path)
        manifest = gate.validate_render_manifest(self.manifest_path, rows)
        evidence = gate.build_case_evidence(
            rows[0],
            gate_id="SYNTHETIC",
            render_map=manifest["adj_0"],
            max_pages=3,
            navigation_budget=1,
            max_chars_per_page=80,
            max_chars_per_case=180,
        )
        self.assertLessEqual(len(evidence.pages), 3)
        self.assertLessEqual(evidence.text_chars, 180)
        self.assertTrue(all(page.snippet_chars <= 80 for page in evidence.pages))
        self.assertLessEqual(len(evidence.navigation_pages), 1)

    def test_outputs_do_not_save_text_prompts_responses_or_secrets(
        self,
    ) -> None:
        self.assertEqual(
            gate.main(self.base_args(self.output_dir) + ["--dry-run"]), 0
        )
        filenames = {
            path.name
            for path in self.output_dir.rglob("*")
            if path.is_file()
        }
        self.assertFalse(any(name.endswith(".txt") for name in filenames))
        self.assertFalse(any("prompt" in name for name in filenames))
        self.assertFalse(any("response" in name for name in filenames))
        metadata_text = (
            self.output_dir
            / "auto_gabriel_adjudication_request_metadata.csv"
        ).read_text(encoding="utf-8")
        self.assertNotIn("fake", metadata_text)
        self.assertNotIn("Authorization", metadata_text)
        self.assertNotIn("Ocp-Apim", metadata_text)

    def test_no_network_calls_except_mocked_live_transport(self) -> None:
        with mock.patch.object(
            gate,
            "run_live_requests",
            side_effect=AssertionError("dry run cannot invoke transport"),
        ):
            gate.main(self.base_args(self.output_dir) + ["--dry-run"])
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertNotIn("requests.get(", source)
        self.assertNotIn("urlopen(", source)
        self.assertNotIn("webbrowser", source)

    def test_inputs_and_durable_ledgers_are_not_mutated(self) -> None:
        protected = [
            REPO_ROOT
            / "docs/analysis/text_table_detection_ledgers"
            / "text_table_detection_ledger_cumulative.csv",
            REPO_ROOT
            / "docs/analysis/pdf_readiness_ledgers"
            / "pdf_readiness_ledger_cumulative.csv",
            REPO_ROOT
            / "docs/analysis/source_review_ledgers"
            / "source_review_ledger_cumulative.csv",
        ]
        before = {path: digest(path) for path in protected}
        gate.main(self.base_args(self.output_dir) + ["--dry-run"])
        self.assertEqual(digest(self.input_path), self.input_hash)
        self.assertEqual(digest(self.manifest_path), self.manifest_hash)
        self.assertEqual(
            {path: digest(path) for path in protected},
            before,
        )

    def test_allowed_values_and_strict_keys_are_enforced(self) -> None:
        parsed = gate.validate_gabriel_response(valid_response())
        self.assertEqual(set(parsed), gate.GABRIEL_RESPONSE_KEYS)
        invalid = json.loads(valid_response())
        invalid["confidence"] = "certain"
        with self.assertRaisesRegex(ValueError, "invalid confidence"):
            gate.validate_gabriel_response(json.dumps(invalid))
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        for values in gate.ALLOWED.values():
            for value in values:
                self.assertIn(value, schema)
        for value in gate.AUTO_GATE_LABELS:
            self.assertIn(value, schema)
        self.assertFalse(gate.GABRIEL_JSON_SCHEMA["additionalProperties"])
        self.assertEqual(
            set(gate.GABRIEL_JSON_SCHEMA["required"]),
            gate.GABRIEL_RESPONSE_KEYS,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
