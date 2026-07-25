#!/usr/bin/env python3
"""Offline synthetic regression tests for Gate 2 navigation/table refinement."""

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

from reportlab.pdfgen import canvas


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "scripts/run_auto_gabriel_text_table_adjudication.py"

spec = importlib.util.spec_from_file_location("auto_gabriel_gate2", RUNNER_PATH)
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def valid_json(**overrides: object) -> str:
    payload: dict[str, object] = {
        "wage_schedule_present": "yes",
        "candidate_page_relationship": "exact_table_page",
        "visual_table_type": "classification_pay_table",
        "non_wage_family": "not_applicable",
        "navigation_needed": "no",
        "navigation_target_found": "not_applicable",
        "extraction_complexity": "easy",
        "extraction_recommendation": "extraction_ready",
        "confidence": "high",
        "reason_codes": ["TABLE_CONFIRMED"],
        "short_rationale": "Bounded role and pay columns form a schedule.",
    }
    payload.update(overrides)
    return json.dumps(payload)


class Gate2RefinementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.pdf_path = self.root / "bounded.pdf"
        pdf = canvas.Canvas(str(self.pdf_path), pagesize=(612, 792))
        for page_number in range(1, 9):
            if page_number == 3:
                pdf.drawString(45, 740, "TABLE OF CONTENTS")
                pdf.drawString(45, 710, "Appendix Salary Schedule ........ 4")
                pdf.drawString(280, 30, "Page 1")
            elif page_number == 6:
                pdf.drawString(45, 740, "Classification Annual Salary")
                for row in range(5):
                    pdf.drawString(
                        45, 700 - 24 * row, f"Officer Rank {row + 1} 50000"
                    )
            else:
                pdf.drawString(45, 740, "Agreement narrative page")
            pdf.showPage()
        pdf.save()
        self.input_path = self.root / "blinded.csv"
        self.manifest_path = self.root / "manifest.csv"
        self.output_dir = self.root / "output"
        self.input_row = {
            "adjudication_case_id": "adj_gate2",
            "calibration_id": "cal_gate2",
            "source_review_id": "sr_gate2",
            "pdf_readiness_id": "pr_gate2",
            "candidate_queue_row_id": "queue_gate2",
            "state": "ZZ",
            "municipality": "Testville",
            "government_name": "City of Testville",
            "unit_type": "police",
            "candidate_source_type": "cba",
            "pdf_page_count": "8",
            "blinded_candidate_pages": "3",
            "blinded_nearby_pages": "2,4",
            "blinded_navigation_pages": "3",
            "content_artifact_path": str(self.pdf_path),
        }
        self.input_fields = list(self.input_row)
        write_csv(self.input_path, self.input_fields, [self.input_row])
        manifest_fields = [
            "adjudication_case_id",
            "calibration_id",
            "page_number",
            "page_role",
            "rendered_image_path",
            "render_status",
            "rendered_bytes",
            "rendered_sha256",
        ]
        write_csv(self.manifest_path, manifest_fields, [])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def args(self, *extra: str) -> list[str]:
        return [
            "--blinded-input-csv",
            str(self.input_path),
            "--render-manifest-csv",
            str(self.manifest_path),
            "--output-dir",
            str(self.output_dir),
            "--gate-id",
            "SYNTHETIC-GATE2",
            "--gate-mode",
            gate.GATE2_MODE,
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
            "--no-save-full-text",
            *extra,
        ]

    def evidence(
        self,
        *,
        diagnostics: list[str],
        table_score: float = 0.8,
        compact_score: float = 0.0,
        role_pay_rows: int = 4,
    ) -> object:
        page = gate.PageEvidence(
            page_number=6,
            role="navigation_target_offset",
            snippet="Classification Annual Salary Officer Rank [NUM]",
            snippet_chars=48,
            wage_terms=3,
            role_terms=4,
            numeric_tokens=6,
            money_tokens=5,
            percent_tokens=0,
            row_like_lines=4,
            column_lines=3,
            header_lines=2,
            geometry_rows=5,
            geometry_columns=3,
            benefit_terms=0,
            budget_terms=0,
            classification_terms=1,
            index_signal=False,
            front_signal=False,
            rendered_available=True,
            image_horizontal_bands=6,
            image_vertical_bands=3,
            image_dark_density=0.1,
            navigation_targets=[],
            role_pay_rows=role_pay_rows,
            aligned_numeric_columns=2,
            compact_role_pay_lines=role_pay_rows,
        )
        source = dict(self.input_row)
        return gate.CaseEvidence(
            source=source,
            auto_id="auto_gate2",
            pages=[page],
            candidate_pages=[3],
            nearby_pages=[],
            navigation_pages=[6],
            text_chars=page.snippet_chars,
            table_score=table_score,
            wage_score=0.8,
            numeric_score=0.8,
            navigation_score=1.0,
            non_wage_score=0.1,
            compact_score=compact_score,
            navigation_targets_found=[6],
            prompt="bounded",
            gate_mode=gate.GATE2_MODE,
            diagnostic_reason_codes=diagnostics,
            printed_page_offsets=[2],
            unresolved_navigation_targets=[],
        )

    def fields(self, **overrides: str) -> dict[str, str]:
        fields = gate.empty_gabriel(
            backend=gate.DEFAULT_BACKEND,
            model=gate.DEFAULT_MODEL,
            status="success",
        )
        fields.update(
            {
                "gabriel_schema_valid": "true",
                "gabriel_wage_schedule_present": "yes",
                "gabriel_candidate_page_relationship": "adjacent_to_table",
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

    def test_gate1_default_mode_remains_backward_compatible(self) -> None:
        parsed = gate.parse_args(
            [
                "--blinded-input-csv",
                str(self.input_path),
                "--render-manifest-csv",
                str(self.manifest_path),
                "--output-dir",
                str(self.output_dir),
                "--gate-id",
                "GATE1-DEFAULT",
            ]
        )
        self.assertEqual(parsed.gate_mode, gate.GATE1_MODE)
        self.assertEqual(gate.LEDGER_FIELDS[-5:], gate.FINAL_FIELDS)

    def test_gate2_dry_run_never_calls_transport_or_saves_prompts(self) -> None:
        with mock.patch.object(
            gate,
            "run_live_requests",
            side_effect=AssertionError("dry run must not call GABRIEL"),
        ):
            self.assertEqual(gate.main(self.args("--dry-run")), 0)
        with (
            self.output_dir / "auto_gabriel_adjudication_ledger.csv"
        ).open(newline="", encoding="utf-8") as handle:
            ledger = list(csv.DictReader(handle))
        self.assertEqual(ledger[0]["gate_mode"], gate.GATE2_MODE)
        names = {path.name for path in self.output_dir.rglob("*") if path.is_file()}
        self.assertFalse(any("prompt" in name or "response" in name for name in names))

    def test_primary_prompt_excludes_prior_labels(self) -> None:
        evidence = gate.build_case_evidence(
            self.input_row,
            gate_id="SYNTHETIC-GATE2",
            render_map={},
            max_pages=6,
            navigation_budget=4,
            max_chars_per_page=1500,
            max_chars_per_case=6000,
            gate_mode=gate.GATE2_MODE,
            candidate_window=1,
        )
        for marker in ("REVIEW1", "REVIEW2", "GATE1", "auto_gate_label"):
            self.assertNotIn(marker, evidence.prompt)

    def test_no_candidate_and_wrong_page_are_distinct_allowed_results(self) -> None:
        no_candidate = json.loads(
            valid_json(
                wage_schedule_present="no",
                candidate_page_relationship="no_candidate_page",
                visual_table_type="no_table",
                non_wage_family="other",
                extraction_complexity="not_extractable",
                extraction_recommendation="exclude_for_now",
            )
        )
        wrong = dict(no_candidate)
        wrong["candidate_page_relationship"] = "wrong_page"
        self.assertEqual(
            gate.validate_gabriel_response(json.dumps(no_candidate))[
                "candidate_page_relationship"
            ],
            "no_candidate_page",
        )
        self.assertEqual(
            gate.validate_gabriel_response(json.dumps(wrong))[
                "candidate_page_relationship"
            ],
            "wrong_page",
        )

    def test_target_outside_budget_is_not_ready(self) -> None:
        evidence = self.evidence(
            diagnostics=["target_table_outside_budget", "insufficient_role_pay_columns"],
            role_pay_rows=0,
            table_score=0.2,
        )
        evidence.navigation_targets_found = []
        result = gate.combine_gate2(
            evidence,
            self.fields(
                gabriel_candidate_page_relationship="points_to_later_table",
                gabriel_navigation_needed="yes",
                gabriel_navigation_target_found="no",
                gabriel_extraction_recommendation="second_review_required",
            ),
        )
        self.assertEqual(result["auto_gate_label"], "second_review_required")
        self.assertIn("TARGET_OUTSIDE_BUDGET", result["auto_gate_reason_codes"])

    def test_compact_role_pay_sheet_can_require_schema_update(self) -> None:
        evidence = self.evidence(
            diagnostics=["compact_compensation_candidate", "true_wage_table_evidence"],
            compact_score=0.9,
        )
        result = gate.combine_gate2(
            evidence,
            self.fields(
                gabriel_visual_table_type="compact_compensation_sheet",
                gabriel_extraction_recommendation="extraction_ready_with_schema_update",
            ),
        )
        self.assertEqual(
            result["auto_gate_label"], "extraction_ready_with_schema_update"
        )

    def test_negative_families_never_become_high_confidence(self) -> None:
        evidence = self.evidence(diagnostics=["true_wage_table_evidence"])
        cases = [
            ("benefits_table", "benefits"),
            ("budget_or_fiscal_table", "budget_or_fiscal"),
            ("classification_without_pay", "classification_without_pay"),
            ("front_matter", "front_matter"),
        ]
        for table_type, family in cases:
            with self.subTest(table_type=table_type):
                result = gate.combine_gate2(
                    evidence,
                    self.fields(
                        gabriel_visual_table_type=table_type,
                        gabriel_non_wage_family=family,
                        gabriel_wage_schedule_present="no",
                        gabriel_extraction_recommendation="exclude_for_now",
                    ),
                )
                self.assertNotEqual(
                    result["auto_gate_label"], "extraction_ready_high_confidence"
                )

    def test_printed_page_offset_is_bounded_and_resolves_target(self) -> None:
        evidence = gate.build_case_evidence(
            self.input_row,
            gate_id="SYNTHETIC-GATE2",
            render_map={},
            max_pages=6,
            navigation_budget=4,
            max_chars_per_page=1500,
            max_chars_per_case=6000,
            gate_mode=gate.GATE2_MODE,
            candidate_window=1,
        )
        self.assertIn("possible_printed_page_offset", evidence.diagnostic_reason_codes)
        self.assertIn(6, evidence.navigation_targets_found)
        self.assertLessEqual(len(evidence.pages), 6)
        self.assertLessEqual(len(evidence.navigation_pages), 4)

    def test_caps_and_strict_schema_failure_are_fail_closed(self) -> None:
        evidence = gate.build_case_evidence(
            self.input_row,
            gate_id="SYNTHETIC-GATE2",
            render_map={},
            max_pages=3,
            navigation_budget=1,
            max_chars_per_page=100,
            max_chars_per_case=250,
            gate_mode=gate.GATE2_MODE,
            candidate_window=1,
        )
        self.assertLessEqual(len(evidence.pages), 3)
        self.assertLessEqual(evidence.text_chars, 250)
        self.assertTrue(all(page.snippet_chars <= 100 for page in evidence.pages))
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            gate.validate_gabriel_response("{bad json")

    def test_prior_outputs_and_durable_ledgers_are_not_mutated(self) -> None:
        protected = [
            REPO_ROOT
            / "docs/analysis/text_table_calibration"
            / "TEXT-TABLE-AUTO-GABRIEL-ADJUDICATION-GATE1-2026-07-24"
            / "auto_gabriel_adjudication_ledger.csv",
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
        input_before = digest(self.input_path)
        gate.main(self.args("--dry-run"))
        self.assertEqual(before, {path: digest(path) for path in protected})
        self.assertEqual(input_before, digest(self.input_path))


if __name__ == "__main__":
    unittest.main(verbosity=2)
