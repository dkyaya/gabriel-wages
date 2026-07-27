#!/usr/bin/env python3
"""Regression tests for the live dashboard content fix/readiness handoff."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/run_live_dashboard_content_audit_fix.py"
SPEC = importlib.util.spec_from_file_location("live_dashboard_content_audit_fix", RUNNER)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LiveDashboardContentAuditFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        mod.main()
        cls.phase = read_json(ROOT / "docs/dashboard/data/project_phase_summary.json")
        cls.reports = read_json(ROOT / "docs/dashboard/data/reports_index.json")
        cls.decision = read_json(mod.OUTPUT / "live_dashboard_content_audit_fix_decision.json")
        cls.scope = read_json(mod.OUTPUT / "tier_c_pdf_text_layer_readiness_scope_summary.json")

    def test_decision_and_counts(self) -> None:
        self.assertEqual(self.decision["decision"], mod.DECISION)
        self.assertEqual(self.decision["tier_c_verified_source_lead_count"], 556)
        self.assertEqual(self.decision["tier_c_retained_source_count"], 463)
        self.assertTrue(self.decision["tier_c_pdf_text_layer_readiness_ready_next"])
        self.assertFalse(self.decision["global_analysis_readiness"])

    def test_completed_download_is_reconciled_not_rerun(self) -> None:
        self.assertEqual(self.scope["source_review_queue_count"], 556)
        self.assertEqual(self.scope["retained_source_count"], 463)
        self.assertEqual(self.scope["retained_file_count_on_disk"], 463)
        self.assertEqual(self.scope["downloads_rerun"], 0)
        self.assertEqual(self.scope["files_opened_or_parsed"], 0)

    def test_dashboard_current_contract(self) -> None:
        self.assertEqual(self.phase["data_vintage"], "2026-07-27")
        self.assertEqual(self.phase["tier_c_verified_source_lead_count"], 556)
        self.assertEqual(self.phase["tier_c_retained_downloaded_source_count"], 463)
        self.assertEqual(self.phase["memo_scope"]["exact_same_source_linked_pair_count"], 268)
        self.assertEqual(self.phase["memo_scope"]["linked_quantitative_row_count"], 208)
        self.assertEqual(self.phase["memo_scope"]["linked_qualitative_record_count"], 90)
        self.assertEqual(self.phase["current_evidence_status"], "bounded_co_location_documentary_scaffold_only")
        self.assertTrue(self.phase["pdf_text_layer_readiness_ready_next"])
        self.assertFalse(self.phase["global_analysis_readiness"])
        self.assertFalse(self.phase["wage_gap_estimates_available"])
        self.assertFalse(self.phase["final_causal_claims_available"])

    def test_current_report_is_memo_and_old_report_is_historical(self) -> None:
        current = [report for report in self.reports["reports"] if report["current"]]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["id"], "bounded-mechanism-linkage-memo-2026-07-26")
        self.assertIn("BOUNDED-INTERNAL-MECHANISM-LINKAGE-CLAIM-MEMO", current[0]["href"])
        old = next(report for report in self.reports["reports"] if report["id"] == "pi-source-discovery-2026-07-22")
        self.assertFalse(old["current"])
        self.assertTrue(old["historical"])

    def test_current_facing_source_has_no_stale_phase_language(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [
                ROOT / "docs/dashboard/src/App.jsx",
                ROOT / "docs/dashboard/src/components/ProjectHubSections.jsx",
                ROOT / "docs/dashboard/src/components/AnalysisReadinessPanel.jsx",
            ]
        )
        for phrase in (
            "Open current PI report",
            "Authorize the first scaled verification round",
            "National source-discovery status",
            "Post-Checkpoint Verification Routing",
            "Current priorities while discovery is paused",
            "Transition from discovery to verified evidence",
            "Scaled verification routing and source triage",
        ):
            self.assertNotIn(phrase, source)
        for phrase in (
            "Current bounded evidence and retained-source status",
            "Bounded Tier C PDF/text-layer readiness review",
            "Historical discovery coverage",
            "Historical candidate queue",
        ):
            self.assertIn(phrase, source)

    def test_local_build_has_current_contract(self) -> None:
        bundles = list((ROOT / "docs/dashboard/dist/assets").glob("index-*.js"))
        self.assertEqual(len(bundles), 1)
        bundle = bundles[0].read_text(encoding="utf-8")
        for phrase in (
            "463 retained sources",
            "verified Tier C leads",
            "Open current evidence memo",
            "Historical candidate queue",
            "Review the retained Tier C text layers",
        ):
            self.assertIn(phrase, bundle)
        self.assertNotIn("Authorize the first scaled verification round", bundle)
        self.assertNotIn("Open current PI report", bundle)

    def test_historical_sections_are_explicit(self) -> None:
        source = (ROOT / "docs/dashboard/src/components/ProjectNavigation.jsx").read_text(encoding="utf-8")
        for label in (
            "Historical coverage",
            "Historical priority tiers",
            "Historical operations",
            "Historical candidate queue",
            "Historical state yield",
        ):
            self.assertIn(label, source)

    def test_forbidden_actions_remain_zero(self) -> None:
        for key in (
            "pdf_pages_accessed",
            "text_extraction_runs",
            "ocr_runs",
            "model_api_calls",
            "rating_runs",
            "ingestion_runs",
            "codification_runs",
            "wage_gap_calculations",
            "regressions_or_treatment_effects",
            "final_causal_or_national_claims",
        ):
            self.assertEqual(self.decision[key], 0)

    def test_next_prompt_preserves_readiness_boundaries(self) -> None:
        prompt = (mod.OUTPUT / "next_targeted_tier_c_pdf_text_layer_readiness_prompt.md").read_text(encoding="utf-8").casefold()
        for phrase in (
            "exactly 463",
            "do not open urls",
            "do not access or render pdf pages",
            "do not run ocr",
            "do not extract evidence spans",
            "do not calculate wage gaps",
            "global analysis readiness remains false",
        ):
            self.assertIn(phrase, prompt)

    def test_partial_package_cannot_masquerade_as_complete(self) -> None:
        required = {
            "live_dashboard_content_audit_fix_decision.json",
            "live_dashboard_content_audit_fix_summary.md",
            "live_dashboard_content_audit.json",
            "dashboard_current_status_contract.json",
            "dashboard_current_status_visibility_check.json",
            "tier_c_pdf_text_layer_readiness_scope_summary.json",
            "live_dashboard_content_audit_fix_invariant_checks.json",
            "next_targeted_tier_c_pdf_text_layer_readiness_prompt.md",
            "next_task.md",
        }
        self.assertEqual(required - {path.name for path in mod.OUTPUT.iterdir()}, set())
        invariants = read_json(mod.OUTPUT / "live_dashboard_content_audit_fix_invariant_checks.json")
        self.assertTrue(all(invariants.values()))

    def test_idempotent_rerun_has_no_output_drift(self) -> None:
        paths = sorted(path for path in mod.OUTPUT.iterdir() if path.is_file())
        before = {path.name: sha(path) for path in paths}
        mod.main()
        after = {path.name: sha(path) for path in paths}
        self.assertEqual(before, after)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LiveDashboardContentAuditFixTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"live dashboard content audit/fix checks: {passed}/{result.testsRun} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
