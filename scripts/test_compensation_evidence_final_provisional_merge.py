#!/usr/bin/env python3
"""Offline tests for the final provisional compensation package merge."""

from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import run_compensation_evidence_final_provisional_merge as merge


class FinalProvisionalMergeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.source_hashes_before = {
            lane: merge.sha_file(merge.INPUT_DIR / spec["input"])
            for lane, spec in merge.INPUT_SPECS.items()
        }
        cls.reconciliation = merge.reconcile_inputs(
            merge.INPUT_DIR, merge.AUTHORITY_PATH
        )
        cls.package = cls.root / "package"
        cls.decision = merge.materialize(
            merge.INPUT_DIR,
            merge.AUTHORITY_PATH,
            cls.package,
            explicitly_authorized=True,
            no_ingestion=True,
            no_codify=True,
            no_analysis=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def copy_inputs(self, target: Path) -> None:
        target.mkdir(parents=True)
        for spec in merge.INPUT_SPECS.values():
            shutil.copyfile(merge.INPUT_DIR / spec["input"], target / spec["input"])

    def test_exactly_five_inputs_and_all_hashes(self) -> None:
        self.assertEqual(len(merge.INPUT_SPECS), 5)
        self.assertEqual(
            set(self.reconciliation["input_sha256"].values()),
            {spec["sha256"] for spec in merge.INPUT_SPECS.values()},
        )

    def test_dry_run_creates_no_output_or_ledger(self) -> None:
        output = self.root / "dry-run-output"
        result = merge.run_dry_run(merge.INPUT_DIR, merge.AUTHORITY_PATH, output)
        self.assertFalse(output.exists())
        self.assertFalse(result["output_directory_created"])
        self.assertEqual(
            result["status"], "dry_run_reconciliation_passed_no_output_written"
        )

    def test_missing_extra_and_hash_mismatch_fail_closed(self) -> None:
        missing = self.root / "missing"
        self.copy_inputs(missing)
        (missing / next(iter(merge.INPUT_SPECS.values()))["input"]).unlink()
        with self.assertRaises(RuntimeError):
            merge.reconcile_inputs(missing, merge.AUTHORITY_PATH)

        extra = self.root / "extra"
        self.copy_inputs(extra)
        (extra / "sixth_ledger_qa_corrected.csv").write_text("x\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            merge.reconcile_inputs(extra, merge.AUTHORITY_PATH)

        changed = self.root / "changed"
        self.copy_inputs(changed)
        name = next(iter(merge.INPUT_SPECS.values()))["input"]
        with (changed / name).open("ab") as handle:
            handle.write(b"\n")
        with self.assertRaises(RuntimeError):
            merge.reconcile_inputs(changed, merge.AUTHORITY_PATH)

    def test_materialization_requires_authorization_and_stop_flags(self) -> None:
        output = self.root / "unauthorized"
        with self.assertRaises(PermissionError):
            merge.materialize(
                merge.INPUT_DIR,
                merge.AUTHORITY_PATH,
                output,
                explicitly_authorized=False,
                no_ingestion=True,
                no_codify=True,
                no_analysis=True,
            )
        self.assertFalse(output.exists())

    def test_outputs_are_byte_identical_and_hash_identical(self) -> None:
        for lane, spec in merge.INPUT_SPECS.items():
            source = merge.INPUT_DIR / spec["input"]
            output = self.package / spec["output"]
            self.assertEqual(source.read_bytes(), output.read_bytes(), lane)
            self.assertEqual(merge.sha_file(output), spec["sha256"])

    def test_expected_source_active_and_case_counts(self) -> None:
        self.assertEqual(
            self.reconciliation["source_counts"],
            {lane: spec["source_rows"] for lane, spec in merge.INPUT_SPECS.items()},
        )
        self.assertEqual(
            self.reconciliation["active_counts"],
            {lane: spec["active_rows"] for lane, spec in merge.INPUT_SPECS.items()},
        )
        self.assertEqual(self.reconciliation["case_count"], 1826)
        self.assertEqual(
            self.reconciliation["unique_readable_content_hash_count"], 1826
        )
        with (self.package / "final_provisional_case_index.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1826)
        self.assertEqual(len({row["document_identity_id"] for row in rows}), 1826)

    def test_provenance_duplicates_pointers_and_contamination(self) -> None:
        value = self.reconciliation
        self.assertEqual(value["duplicate_observation_id_count"], 0)
        self.assertEqual(value["duplicate_provenance_row_count"], 14)
        self.assertEqual(value["newly_canonicalized_duplicate_count"], 5)
        self.assertEqual(value["invalid_bounded_page_pointer_count"], 0)
        self.assertEqual(value["base_non_base_wage_contamination_count"], 0)
        self.assertEqual(value["working_out_of_classification_reroute_count"], 3)
        self.assertEqual(value["wasco_record_boundary_repair_count"], 1)

    def test_mixed_joins_and_inactive_rows_are_preserved(self) -> None:
        self.assertEqual(self.reconciliation["source_counts"]["mixed"], 387)
        self.assertEqual(self.reconciliation["active_counts"]["mixed"], 371)
        self.assertEqual(
            self.reconciliation["historical_mixed_key_provenance_count"], 5
        )
        self.assertTrue(
            any(
                row["has_inactive_provenance_rows"] == "true"
                for row in self.reconciliation["case_index"]
            )
        )

    def test_two_unresolved_groups_remain_explicit(self) -> None:
        self.assertEqual(self.reconciliation["unresolved_conflict_group_count"], 2)
        fields, rows = merge.read_csv(
            self.package / "final_provisional_conflict_register.csv"
        )
        self.assertEqual(fields, merge.CONFLICT_FIELDS)
        self.assertEqual({row["resolution_id"] for row in rows}, set(merge.EXPECTED_UNRESOLVED))
        self.assertTrue(all(row["resolution_status"] == "unresolved" for row in rows))
        self.assertTrue(
            all(row["ambiguity_preservation"] == "preserved_without_inference" for row in rows)
        )

    def test_representation_and_ocr_exclusion(self) -> None:
        self.assertEqual(self.reconciliation["unit_type_counts"], merge.EXPECTED_UNIT_COUNTS)
        self.assertEqual(self.reconciliation["state_count"], 51)
        self.assertEqual(self.reconciliation["source_family_counts"], merge.EXPECTED_SOURCE_COUNTS)
        self.assertTrue(self.decision["ocr_later_documents_excluded"])

    def test_package_remains_provisional_and_analysis_closed(self) -> None:
        decision = json.loads(
            (self.package / "final_provisional_decision.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            decision["decision"], "final_provisional_package_materialized_qa_pass"
        )
        self.assertFalse(decision["final_analysis_ready"])
        self.assertFalse(decision["ingestion_allowed"])
        self.assertFalse(decision["codify_allowed"])
        self.assertFalse(decision["wage_gap_analysis_allowed"])
        self.assertFalse(decision["regression_allowed"])

    def test_case_index_is_non_analytic(self) -> None:
        fields, _ = merge.read_csv(self.package / "final_provisional_case_index.csv")
        forbidden = {
            "rate_value", "salary_value", "hourly_rate", "annual_salary",
            "percentage_increase", "mechanism_type", "bounded_evidence_text",
        }
        self.assertFalse(forbidden & set(fields))

    def test_no_network_model_ocr_ingestion_or_extraction_code_path(self) -> None:
        source = Path(merge.__file__).read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests", "import httpx", "urllib.request", "socket.",
            "call_gabriel(", "ocrmypdf", "process_inbox(", "gabriel.codify(",
            "run_live_extraction(", "freeze_selection(",
        ):
            self.assertNotIn(forbidden, source)

    def test_approved_sources_remain_unchanged(self) -> None:
        after = {
            lane: merge.sha_file(merge.INPUT_DIR / spec["input"])
            for lane, spec in merge.INPUT_SPECS.items()
        }
        self.assertEqual(self.source_hashes_before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
