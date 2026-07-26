#!/usr/bin/env python3
"""Focused adversarial tests for bounded qualitative span disambiguation."""

from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import run_compensation_evidence_bounded_qualitative_span_disambiguation_followup as mod
import run_compensation_evidence_bounded_local_pdf_text_layer_span_capture as prior


def row(**updates: str) -> dict[str, str]:
    base = {field: "" for field in mod.STRUCTURED_FIELDS}
    base.update({
        "qualitative_observation_id": "lobs_test",
        "mechanism_type": "step_movement_or_seniority",
        "step_progression_rule": "Step progression",
    })
    base.update(updates)
    return base


def prior_row(status: str = "span_ambiguous_multiple_candidates") -> dict[str, str]:
    text = "Step progression"
    return {
        "qualitative_observation_id": "lobs_test",
        "extraction_case_id": "cex_test",
        "document_identity_id": "doc_test",
        "source_review_id": "sr_test",
        "text_table_detection_id": "ttd_test",
        "retained_content_hash": "a" * 64,
        "pdf_sha256": "a" * 64,
        "page_number": "1",
        "bounded_evidence_pointer": "artifact.pdf#page=1",
        "mechanism_type": "step_movement_or_seniority",
        "literal_verbatim_evidence_span": text if status != "span_unavailable_or_unverified" else "",
        "span_start": "0" if status != "span_unavailable_or_unverified" else "",
        "span_end": str(len(text)) if status != "span_unavailable_or_unverified" else "",
        "span_length": str(len(text)) if status != "span_unavailable_or_unverified" else "0",
        "span_sha256": mod.text_sha256(text) if status != "span_unavailable_or_unverified" else "",
        "span_capture_status": status,
        "span_failure_reason": "" if status != "span_unavailable_or_unverified" else "no match",
        "span_capture_reason_code": "prior",
        "span_candidate_count": "2" if status == "span_ambiguous_multiple_candidates" else "0",
        "span_qa_pass": "true" if status == "exact_verified" else "false",
        "qa_status": "exact_literal_span_verified" if status == "exact_verified" else "navigation_only_span_not_qa_sufficient",
    }


class CandidateRuleTests(unittest.TestCase):
    def test_repeated_anchor_unique_mechanism_compensation_context_resolves(self) -> None:
        page = "Step progression governs leave requests. Step progression increases the pay rate annually."
        result = mod.disambiguate(row(), page, prior_row())
        self.assertEqual(result["span_capture_status"], "exact_verified")
        self.assertIn("pay rate", result["literal_verbatim_evidence_span"])
        self.assertEqual(result["span_qa_status"], "span_exact_unique_verified")

    def test_repeated_anchor_equal_context_remains_ambiguous(self) -> None:
        page = "Step progression increases the pay rate annually. Step progression increases the pay rate monthly."
        result = mod.disambiguate(row(), page, prior_row())
        self.assertEqual(result["span_capture_status"], "span_ambiguous_multiple_candidates")
        self.assertEqual(result["span_disambiguation_action"], "remains_ambiguous")

    def test_unavailable_no_exact_support_remains_unavailable(self) -> None:
        page = "The parties discuss unrelated scheduling procedures."
        result = mod.disambiguate(row(), page, prior_row("span_unavailable_or_unverified"))
        self.assertEqual(result["span_capture_status"], "span_unavailable_or_unverified")
        self.assertEqual(result["span_disambiguation_action"], "remains_unavailable")

    def test_exact_token_fallback_can_resolve_unavailable(self) -> None:
        r = row(step_progression_rule="Employees progress to the next step annually based on seniority")
        page = "Header material. Employees progress to the next step annually based on seniority and receive a higher pay rate. Footer material."
        result = mod.disambiguate(r, page, prior_row("span_unavailable_or_unverified"))
        self.assertEqual(result["span_capture_status"], "exact_verified")
        self.assertIn(result["literal_verbatim_evidence_span"], page)

    def test_fuzzy_or_paraphrased_match_is_rejected(self) -> None:
        r = row(step_progression_rule="Employees advance annually based on seniority")
        page = "Workers move every year according to length of service and obtain higher compensation."
        result = mod.disambiguate(r, page, prior_row("span_unavailable_or_unverified"))
        self.assertNotEqual(result["span_capture_status"], "exact_verified")

    def test_cross_line_candidate_is_rejected(self) -> None:
        r = row(step_progression_rule="Step progression increases pay")
        page = "Step progression\nincreases pay annually."
        result = mod.disambiguate(r, page, prior_row("span_unavailable_or_unverified"))
        self.assertNotEqual(result["span_capture_status"], "exact_verified")

    def test_new_exact_span_round_trips_and_hashes(self) -> None:
        page = "Header material. Step progression increases the pay rate annually. Footer material."
        result = mod.disambiguate(row(), page, prior_row())
        text = result["literal_verbatim_evidence_span"]
        self.assertEqual(page[int(result["span_start"]):int(result["span_end"])], text)
        self.assertEqual(result["span_sha256"], hashlib.sha256(text.encode()).hexdigest())
        self.assertNotIn("\n", text)

    def test_full_page_leakage_is_rejected(self) -> None:
        text = "Step progression increases pay."
        result = prior.span_result("exact_verified", "test", 0, len(text), text, 1)
        with self.assertRaises(RuntimeError):
            prior.verify_span(text, result)


class PreservationAndGuardTests(unittest.TestCase):
    def test_prior_verified_internal_invariants_pass(self) -> None:
        mod.verify_prior_verified(prior_row("exact_verified"))

    def test_prior_verified_hash_mismatch_fails_closed(self) -> None:
        item = prior_row("exact_verified")
        item["span_sha256"] = "0" * 64
        with self.assertRaises(RuntimeError):
            mod.verify_prior_verified(item)

    def test_prior_verified_offset_mismatch_fails_closed(self) -> None:
        item = prior_row("exact_verified")
        item["span_end"] = "999"
        with self.assertRaises(RuntimeError):
            mod.verify_prior_verified(item)

    def test_approved_page_guard_rejects_non_target(self) -> None:
        approved = prior.ApprovedPage(Path("a.pdf"), "a" * 64, 1)
        other = prior.ApprovedPage(Path("a.pdf"), "a" * 64, 2)
        guard = prior.PageAccessGuard({approved}, lambda _: None)
        with self.assertRaises(RuntimeError):
            guard.extract(other)

    def test_output_boundary_rejects_tmp(self) -> None:
        with self.assertRaises(RuntimeError):
            mod.output_guard(Path(tempfile.gettempdir()) / "bad-output")

    def test_checkpoint_rejects_page_text(self) -> None:
        with tempfile.TemporaryDirectory(dir=mod.ROOT / "tmp") as temp:
            path = Path(temp) / "checkpoint.jsonl"
            path.write_text(json.dumps({
                "schema_version": mod.SCHEMA_VERSION,
                "input_signature": "sig",
                "qualitative_observation_id": "lobs_test",
                "page_text": "forbidden",
            }) + "\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                mod.load_checkpoint(path, "sig")

    def test_checkpoint_schema_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=mod.ROOT / "tmp") as temp:
            path = Path(temp) / "checkpoint.jsonl"
            path.write_text(json.dumps({
                "schema_version": "old",
                "input_signature": "sig",
                "qualitative_observation_id": "lobs_test",
            }) + "\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                mod.load_checkpoint(path, "sig")

    def test_checkpoint_duplicate_id_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir=mod.ROOT / "tmp") as temp:
            path = Path(temp) / "checkpoint.jsonl"
            item = {"schema_version": mod.SCHEMA_VERSION, "input_signature": "sig", "qualitative_observation_id": "lobs_test"}
            path.write_text(json.dumps(item) + "\n" + json.dumps(item) + "\n", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                mod.load_checkpoint(path, "sig")

    def test_checkpoint_roundtrip_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(dir=mod.ROOT / "tmp") as temp:
            path = Path(temp) / "checkpoint.jsonl"
            item = {"schema_version": mod.SCHEMA_VERSION, "input_signature": "sig", "qualitative_observation_id": "lobs_test"}
            mod.append_checkpoint(path, item)
            self.assertEqual(mod.load_checkpoint(path, "sig"), {"lobs_test": item})
            self.assertEqual(mod.load_checkpoint(path, "sig"), {"lobs_test": item})

    def test_checkpoint_signature_is_stable_and_scope_sensitive(self) -> None:
        info = {"input_hashes": {"x": "a" * 64}, "review_rows": [{"qualitative_observation_id": "one"}]}
        self.assertEqual(mod.signature(info), mod.signature(info))
        changed = {**info, "review_rows": [{"qualitative_observation_id": "two"}]}
        self.assertNotEqual(mod.signature(info), mod.signature(changed))


class RepositoryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prior_hashes = {name: mod.sha256(path) for name, path in mod.INPUTS.items()}
        cls.package_hashes = {name: mod.sha256(path) for name, path in prior.PACKAGE_LEDGERS.items()}

    def test_preflight_frozen_counts_and_hashes(self) -> None:
        out = mod.ROOT / "docs/analysis/compensation_extraction/TEST-BOUNDED-QUALITATIVE-SPAN-DISAMBIGUATION-PREFLIGHT"
        self.assertFalse(out.exists())
        info = mod.preflight(out)
        self.assertEqual(info["prior_status_counts"], mod.EXPECTED_PRIOR)
        self.assertEqual(len(info["review_rows"]), 1499)
        self.assertEqual(len(info["ledger_rows"]), 1954)
        self.assertEqual(info["package_hashes"], prior.EXPECTED_PACKAGE_SHA256)
        self.assertFalse(out.exists())

    def test_prior_and_package_inputs_remain_unmodified(self) -> None:
        self.assertEqual(self.prior_hashes, {name: mod.sha256(path) for name, path in mod.INPUTS.items()})
        self.assertEqual(self.package_hashes, {name: mod.sha256(path) for name, path in prior.PACKAGE_LEDGERS.items()})

    def test_prior_verified_count_and_content_contract(self) -> None:
        _, rows = mod.read_csv(mod.INPUTS["ledger"])
        verified = [item for item in rows if item["span_capture_status"] == "exact_verified"]
        self.assertEqual(len(verified), 455)
        for item in verified:
            mod.verify_prior_verified(item)

    def test_carried_forward_row_counts(self) -> None:
        expected = {"quant_candidate": 862, "quant_exception": 1045, "nonbase": 4733, "reference": 345}
        for name, count in expected.items():
            _, rows = mod.read_csv(mod.INPUTS[name])
            self.assertEqual(len(rows), count)
        _, conflicts = mod.read_csv(mod.INPUTS["conflicts"])
        self.assertEqual(len(conflicts), 2)

    def test_analysis_readiness_is_false(self) -> None:
        decision = json.loads(mod.INPUTS["decision"].read_text(encoding="utf-8"))
        self.assertIs(decision["analysis_readiness"], False)
        self.assertIs(decision["repeat_analysis_readiness_review_allowed"], False)

    def test_no_coded_qualitative_view_in_prior(self) -> None:
        self.assertFalse((mod.PRIOR_DIR / "qualitative_mechanism_analysis_view_candidate.csv").exists())

    def test_materialized_output_counts_and_statuses(self) -> None:
        _, rows = mod.read_csv(mod.DEFAULT_OUTPUT / mod.OUTPUTS["ledger"])
        self.assertEqual(len(rows), 1954)
        self.assertEqual(len({r["qualitative_observation_id"] for r in rows}), 1954)
        self.assertEqual(
            {k: sum(r["span_capture_status"] == k for r in rows) for k in mod.EXPECTED_PRIOR},
            {"exact_verified": 759, "span_ambiguous_multiple_candidates": 614, "span_unavailable_or_unverified": 581},
        )

    def test_materialized_prior_verified_rows_are_preserved(self) -> None:
        _, old = mod.read_csv(mod.INPUTS["ledger"])
        _, new = mod.read_csv(mod.DEFAULT_OUTPUT / mod.OUTPUTS["ledger"])
        new_by_id = {r["qualitative_observation_id"]: r for r in new}
        for prior_item in old:
            if prior_item["span_capture_status"] != "exact_verified":
                continue
            current = new_by_id[prior_item["qualitative_observation_id"]]
            for field, value in prior_item.items():
                self.assertEqual(current[field], value)
            self.assertEqual(current["span_disambiguation_action"], "preserved_prior_verified")

    def test_materialized_page_audit_is_strictly_bounded(self) -> None:
        summary = json.loads((mod.DEFAULT_OUTPUT / mod.OUTPUTS["page_summary"]).read_text(encoding="utf-8"))
        self.assertEqual(summary["review_row_count"], 1499)
        self.assertEqual(summary["unique_approved_review_page_count"], 1011)
        self.assertEqual(summary["unique_review_pages_accounted_for"], 1011)
        self.assertEqual(summary["ocr_later_access_count"], 0)
        self.assertEqual(summary["non_target_page_access_count"], 0)
        self.assertEqual(summary["page_text_persisted_count"], 0)

    def test_materialized_carry_files_are_byte_identical(self) -> None:
        mapping = {"quant_candidate": "quant_candidate", "quant_exception": "quant_exception", "nonbase": "nonbase", "reference": "reference", "conflicts": "conflicts", "residual": "residual"}
        for output_name, input_name in mapping.items():
            self.assertEqual(mod.sha256(mod.DEFAULT_OUTPUT / mod.OUTPUTS[output_name]), mod.sha256(mod.INPUTS[input_name]))

    def test_materialized_output_has_no_page_text_or_multiline_spans(self) -> None:
        header, rows = mod.read_csv(mod.DEFAULT_OUTPUT / mod.OUTPUTS["ledger"])
        self.assertFalse({"page_text", "full_page_text", "raw_page_text"} & set(header))
        self.assertTrue(all("\n" not in r["literal_verbatim_evidence_span"] and "\r" not in r["literal_verbatim_evidence_span"] for r in rows))

    def test_materialized_no_coded_view_and_readiness_false(self) -> None:
        decision = json.loads((mod.DEFAULT_OUTPUT / mod.OUTPUTS["decision"]).read_text(encoding="utf-8"))
        self.assertIs(decision["analysis_readiness"], False)
        self.assertIs(decision["repeat_analysis_readiness_review_allowed"], False)
        self.assertFalse((mod.DEFAULT_OUTPUT / "qualitative_mechanism_analysis_view_candidate.csv").exists())

    def test_complete_output_resume_reuses_without_pdf_access(self) -> None:
        info = mod.preflight(mod.DEFAULT_OUTPUT, allow_existing=True)
        reused = mod.reuse_complete(mod.DEFAULT_OUTPUT, info)
        self.assertIs(reused["idempotent_complete_output_reused"], True)
        self.assertEqual(reused["pdf_pages_reaccessed_on_reuse"], 0)

    def test_materialized_span_hash_offset_and_length_contract(self) -> None:
        _, rows = mod.read_csv(mod.DEFAULT_OUTPUT / mod.OUTPUTS["ledger"])
        for item in rows:
            text = item["literal_verbatim_evidence_span"]
            if not text:
                continue
            self.assertEqual(item["span_sha256"], mod.text_sha256(text))
            self.assertEqual(int(item["span_length"]), len(text))
            self.assertEqual(int(item["span_end"]) - int(item["span_start"]), len(text))


if __name__ == "__main__":
    unittest.main(verbosity=2)
